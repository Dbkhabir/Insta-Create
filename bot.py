"""
Telegram Bot for Instagram Account Creator.
Full Automation Enabled Version.
"""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        CallbackQueryHandler,
        MessageHandler,
        ConversationHandler,
        ContextTypes,
        filters
    )
    logger.info("Telegram libraries imported")
except ImportError as e:
    logger.error(f"Failed to import telegram: {e}")
    sys.exit(1)

from typing import Dict, Any
import asyncio
import traceback

try:
    from config import Config
    from user_config import UserConfig, UsernameMode, FullNameMode
    from password_manager import PasswordMode
    from email_providers import EmailProviderManager
    from captcha_solver import CaptchaSolver
    from utils import estimate_creation_time, format_time, get_progress_bar
    logger.info("Project modules imported")
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    traceback.print_exc()
    sys.exit(1)

# Conversation states
(
    MAIN_MENU,
    QUANTITY_SELECT,
    USERNAME_SELECT,
    USERNAME_INPUT,
    FULLNAME_SELECT,
    FULLNAME_INPUT,
    PASSWORD_SELECT,
    PASSWORD_INPUT,
    CONFIRM_CREATE
) = range(9)


class InstagramBot:
    """Main Telegram bot class."""
    
    def __init__(self):
        """Initialize bot."""
        try:
            self.user_configs: Dict[int, UserConfig] = {}
            self.email_manager = EmailProviderManager()
            self.captcha_solver = CaptchaSolver()
            logger.info("InstagramBot initialized")
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise
    
    def get_user_config(self, user_id: int) -> UserConfig:
        """Get or create user configuration."""
        if user_id not in self.user_configs:
            self.user_configs[user_id] = UserConfig()
        return self.user_configs[user_id]
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        try:
            welcome_text = (
                "🎉 <b>Welcome to Instagram Account Creator Bot!</b>\n\n"
                "This bot helps you create Instagram accounts automatically.\n\n"
                "<b>✨ Features:</b>\n"
                "• Create 1-50 accounts at once\n"
                "• Custom or random passwords\n"
                "• Flexible username options\n"
                "• 12 reliable email providers\n"
                "• Smart captcha solving\n"
                "• Real-time progress updates\n\n"
                "<b>📱 Commands:</b>\n"
                "/create - Start creating accounts\n"
                "/status - Check system status\n"
                "/help - Get help\n"
                "/cancel - Cancel operation\n\n"
                "👉 Click /create to get started!"
            )
            
            await update.message.reply_text(welcome_text, parse_mode='HTML')
            logger.info(f"User {update.effective_user.id} started the bot")
            
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await update.message.reply_text("Error occurred. Please try again.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_text = (
            "📖 <b>Help Guide</b>\n\n"
            "<b>🚀 How to use:</b>\n"
            "1. Use /create to start\n"
            "2. Choose number of accounts\n"
            "3. Configure username\n"
            "4. Configure full name\n"
            "5. Choose password mode\n"
            "6. Confirm and start\n\n"
            "<b>💡 Tips:</b>\n"
            "• Start with 1 account to test\n"
            "• Random passwords are more secure\n"
            "• Be patient, it takes time\n"
        )
        
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command."""
        try:
            status_text = "📊 <b>System Status</b>\n\n"
            status_text += self.email_manager.get_provider_status()
            await update.message.reply_text(status_text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Error in status: {e}")
            await update.message.reply_text(f"Error: {str(e)}")
    
    async def create_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /create command."""
        try:
            keyboard = [
                [
                    InlineKeyboardButton("1 Account", callback_data="qty_1"),
                    InlineKeyboardButton("5 Accounts", callback_data="qty_5"),
                ],
                [
                    InlineKeyboardButton("10 Accounts", callback_data="qty_10"),
                    InlineKeyboardButton("Custom", callback_data="qty_custom"),
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = (
                "🔢 <b>How many accounts?</b>\n\n"
                "Select option or choose custom (1-50):"
            )
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
            return QUANTITY_SELECT
            
        except Exception as e:
            logger.error(f"Error in create: {e}")
            await update.message.reply_text("Error occurred.")
            return ConversationHandler.END
    
    async def quantity_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle quantity selection."""
        query = update.callback_query
        await query.answer()
        
        try:
            user_id = query.from_user.id
            user_config = self.get_user_config(user_id)
            data = query.data
            
            if data == "qty_custom":
                await query.edit_message_text("🔢 Enter number (1-50):", parse_mode='HTML')
                return QUANTITY_SELECT
            
            elif data.startswith("qty_"):
                num = int(data.split("_")[1])
                user_config.set_account_quantity(num)
                estimated_time = estimate_creation_time(num)
                
                keyboard = [
                    [InlineKeyboardButton("Fully Random", callback_data="username_random")],
                    [InlineKeyboardButton("Custom Prefix", callback_data="username_prefix")],
                    [InlineKeyboardButton("Custom List", callback_data="username_list")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                text = (
                    f"✅ Creating <b>{num}</b> accounts\n"
                    f"⏱ Time: ~{format_time(estimated_time)}\n\n"
                    "👤 <b>Username mode:</b>\n\n"
                    "• Random: alex_8492\n"
                    "• Prefix: mybrand_8492\n"
                    "• List: Your usernames"
                )
                
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
                return USERNAME_SELECT
                
        except Exception as e:
            logger.error(f"Error: {e}")
            await query.edit_message_text("Error occurred.")
            return ConversationHandler.END
    
    async def quantity_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle custom quantity."""
        try:
            num = int(update.message.text)
            if num < 1 or num > 50:
                await update.message.reply_text("Enter 1-50")
                return QUANTITY_SELECT
            
            user_id = update.message.from_user.id
            user_config = self.get_user_config(user_id)
            user_config.set_account_quantity(num)
            
            keyboard = [
                [InlineKeyboardButton("Fully Random", callback_data="username_random")],
                [InlineKeyboardButton("Custom Prefix", callback_data="username_prefix")],
                [InlineKeyboardButton("Custom List", callback_data="username_list")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = f"✅ Creating {num} accounts\n\n👤 Username mode:"
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
            return USERNAME_SELECT
            
        except ValueError:
            await update.message.reply_text("Enter valid number")
            return QUANTITY_SELECT
    
    async def username_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle username mode."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_config = self.get_user_config(user_id)
        data = query.data
        
        if data == "username_random":
            user_config.set_username_mode(UsernameMode.RANDOM)
            return await self._show_fullname_menu(query, user_config)
        
        elif data == "username_prefix":
            await query.edit_message_text("📝 Enter prefix:\n\nExample: mybrand", parse_mode='HTML')
            context.user_data['username_mode'] = 'prefix'
            return USERNAME_INPUT
        
        elif data == "username_list":
            await query.edit_message_text(
                f"📝 Send {user_config.num_accounts} usernames (one per line)",
                parse_mode='HTML'
            )
            context.user_data['username_mode'] = 'list'
            return USERNAME_INPUT
    
    async def username_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle username input."""
        user_id = update.message.from_user.id
        user_config = self.get_user_config(user_id)
        mode = context.user_data.get('username_mode')
        
        if mode == 'prefix':
            prefix = update.message.text.strip()
            user_config.set_username_mode(UsernameMode.PREFIX, prefix=prefix)
            await update.message.reply_text(f"✅ Prefix: {prefix}")
            
        elif mode == 'list':
            usernames = [line.strip() for line in update.message.text.split('\n') if line.strip()]
            if len(usernames) < user_config.num_accounts:
                await update.message.reply_text(f"Need {user_config.num_accounts} usernames")
                return USERNAME_INPUT
            user_config.set_username_mode(UsernameMode.LIST, custom_list=usernames)
            await update.message.reply_text(f"✅ {len(usernames)} usernames saved")
        
        return await self._show_fullname_menu_message(update, user_config)
    
    async def _show_fullname_menu(self, query, user_config) -> int:
        """Show fullname menu."""
        keyboard = [
            [InlineKeyboardButton("Random Names", callback_data="fullname_random")],
            [InlineKeyboardButton("Same Name", callback_data="fullname_same")],
            [InlineKeyboardButton("Custom List", callback_data="fullname_list")],
            [InlineKeyboardButton("Empty", callback_data="fullname_empty")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "📝 <b>Full name mode:</b>"
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return FULLNAME_SELECT
    
    async def _show_fullname_menu_message(self, update, user_config) -> int:
        """Show fullname menu (message)."""
        keyboard = [
            [InlineKeyboardButton("Random Names", callback_data="fullname_random")],
            [InlineKeyboardButton("Same Name", callback_data="fullname_same")],
            [InlineKeyboardButton("Custom List", callback_data="fullname_list")],
            [InlineKeyboardButton("Empty", callback_data="fullname_empty")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "📝 <b>Full name mode:</b>"
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return FULLNAME_SELECT
    
    async def fullname_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle fullname mode."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_config = self.get_user_config(user_id)
        data = query.data
        
        if data == "fullname_random":
            user_config.set_fullname_mode(FullNameMode.RANDOM)
            return await self._show_password_menu(query, user_config)
        
        elif data == "fullname_empty":
            user_config.set_fullname_mode(FullNameMode.EMPTY)
            return await self._show_password_menu(query, user_config)
        
        elif data == "fullname_same":
            await query.edit_message_text("📝 Enter name for all accounts:", parse_mode='HTML')
            context.user_data['fullname_mode'] = 'same'
            return FULLNAME_INPUT
        
        elif data == "fullname_list":
            await query.edit_message_text(
                f"📝 Send {user_config.num_accounts} names (one per line)",
                parse_mode='HTML'
            )
            context.user_data['fullname_mode'] = 'list'
            return FULLNAME_INPUT
    
    async def fullname_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle fullname input."""
        user_id = update.message.from_user.id
        user_config = self.get_user_config(user_id)
        mode = context.user_data.get('fullname_mode')
        
        if mode == 'same':
            name = update.message.text.strip()
            user_config.set_fullname_mode(FullNameMode.SAME, same_name=name)
            await update.message.reply_text(f"✅ Name: {name}")
            
        elif mode == 'list':
            names = [line.strip() for line in update.message.text.split('\n') if line.strip()]
            if len(names) < user_config.num_accounts:
                await update.message.reply_text(f"Need {user_config.num_accounts} names")
                return FULLNAME_INPUT
            user_config.set_fullname_mode(FullNameMode.LIST, custom_list=names)
            await update.message.reply_text(f"✅ {len(names)} names saved")
        
        return await self._show_password_menu_message(update, user_config)
    
    async def _show_password_menu(self, query, user_config) -> int:
        """Show password menu."""
        keyboard = [
            [InlineKeyboardButton("🔒 Custom (Same for All)", callback_data="password_custom")],
            [InlineKeyboardButton("🎲 Random (Unique Each)", callback_data="password_random")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "🔐 <b>Password mode:</b>\n\n"
            "• Custom: Same password for all\n"
            "• Random: Unique password each"
        )
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return PASSWORD_SELECT
    
    async def _show_password_menu_message(self, update, user_config) -> int:
        """Show password menu (message)."""
        keyboard = [
            [InlineKeyboardButton("🔒 Custom (Same)", callback_data="password_custom")],
            [InlineKeyboardButton("🎲 Random (Unique)", callback_data="password_random")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = "🔐 <b>Password mode:</b>"
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return PASSWORD_SELECT
    
    async def password_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle password mode."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_config = self.get_user_config(user_id)
        data = query.data
        
        if data == "password_random":
            user_config.set_password_config(PasswordMode.RANDOM)
            return await self._show_confirmation(query, user_config)
        
        elif data == "password_custom":
            await query.edit_message_text("🔒 Enter password (min 6 chars):", parse_mode='HTML')
            return PASSWORD_INPUT
    
    async def password_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle password input."""
        user_id = update.message.from_user.id
        user_config = self.get_user_config(user_id)
        password = update.message.text
        
        is_valid, error = user_config.password_manager.validate_password(password)
        
        if not is_valid:
            await update.message.reply_text(f"❌ {error}\n\nTry again:")
            return PASSWORD_INPUT
        
        user_config.set_password_config(PasswordMode.CUSTOM, custom_password=password)
        
        try:
            await update.message.delete()
        except:
            pass
        
        await update.message.reply_text("✅ Password set!")
        
        return await self._show_confirmation_message(update, user_config)
    
    async def _show_confirmation(self, query, user_config) -> int:
        """Show confirmation."""
        summary = user_config.get_summary()
        
        keyboard = [
            [InlineKeyboardButton("✅ Start Creating", callback_data="confirm_yes")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"{summary}\n\n<b>Ready?</b>"
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return CONFIRM_CREATE
    
    async def _show_confirmation_message(self, update, user_config) -> int:
        """Show confirmation (message)."""
        summary = user_config.get_summary()
        
        keyboard = [
            [InlineKeyboardButton("✅ Start Creating", callback_data="confirm_yes")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"{summary}\n\n<b>Ready?</b>"
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return CONFIRM_CREATE
    
    async def confirm_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle confirmation."""
        query = update.callback_query
        await query.answer()
        
        try:
            if query.data == "confirm_yes":
                user_id = query.from_user.id
                user_config = self.get_user_config(user_id)
                
                await query.edit_message_text(
                    "🚀 <b>Starting account creation...</b>\n\n"
                    "⏳ Please wait, this may take several minutes.\n"
                    "You will receive updates during the process.",
                    parse_mode='HTML'
                )
                
                logger.info(f"User {user_id} starting creation: {user_config.num_accounts} accounts")
                
                try:
                    await self._create_accounts(query, user_config)
                except Exception as e:
                    logger.error(f"Error in creation: {e}")
                    traceback.print_exc()
                    await query.message.reply_text(
                        f"❌ <b>Error:</b>\n\n{str(e)}\n\n"
                        "Try with fewer accounts or check logs.",
                        parse_mode='HTML'
                    )
                
                return ConversationHandler.END
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error in confirm: {e}")
            await query.edit_message_text("Error occurred.")
            return ConversationHandler.END
    
    async def _create_accounts(self, query, user_config: UserConfig) -> None:
        """Create accounts with progress updates."""
        chat_id = query.message.chat_id
        progress_message = None
        
        async def progress_callback(data: Dict[str, Any]):
            nonlocal progress_message
            
            message = data.get('message', '')
            percentage = data.get('percentage')
            account = data.get('account', 0)
            total = data.get('total', 0)
            
            text = f"{message}\n\n"
            
            if percentage is not None:
                progress_bar = get_progress_bar(account, total)
                text += f"{progress_bar}\n"
                text += f"Account: {account}/{total}"
            
            try:
                if progress_message is None:
                    progress_message = await query.message.reply_text(text)
                else:
                    await progress_message.edit_text(text)
            except Exception as e:
                logger.error(f"Error updating progress: {e}")
        
        try:
            from instagram_creator import InstagramCreator
            
            creator = InstagramCreator(user_config, progress_callback)
            summary = await asyncio.to_thread(creator.create_accounts)
            
            result_text = (
                "✨ <b>Completed!</b>\n\n"
                f"✅ Success: {summary['successful']}\n"
                f"❌ Failed: {summary['failed']}\n"
                f"⏱ Time: {format_time(summary['elapsed_time'])}\n\n"
            )
            
            if summary['successful'] > 0:
                result_text += "<b>Created Accounts:</b>\n"
                for acc in summary['accounts'][:5]:
                    result_text += f"• @{acc['username']}\n"
                
                if len(summary['accounts']) > 5:
                    result_text += f"... +{len(summary['accounts']) - 5} more\n"
                
                result_text += f"\n💾 Saved to {Config.CREDENTIALS_FILE}"
            
            await query.message.reply_text(result_text, parse_mode='HTML')
            
        except ImportError:
            await query.message.reply_text(
                "⚠️ Instagram creator not available.\n"
                "Check deployment logs.",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            traceback.print_exc()
            raise
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /cancel."""
        await update.message.reply_text("❌ Cancelled.")
        return ConversationHandler.END
    
    async def cancel_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle cancel button."""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ Cancelled.")
        return ConversationHandler.END
    
    def run(self):
        """Run the bot."""
        try:
            logger.info("Creating application...")
            application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
            
            conv_handler = ConversationHandler(
                entry_points=[CommandHandler('create', self.create_command)],
                states={
                    QUANTITY_SELECT: [
                        CallbackQueryHandler(self.quantity_callback, pattern='^qty_'),
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.quantity_message),
                    ],
                    USERNAME_SELECT: [
                        CallbackQueryHandler(self.username_callback, pattern='^username_'),
                    ],
                    USERNAME_INPUT: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.username_input),
                    ],
                    FULLNAME_SELECT: [
                        CallbackQueryHandler(self.fullname_callback, pattern='^fullname_'),
                    ],
                    FULLNAME_INPUT: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.fullname_input),
                    ],
                    PASSWORD_SELECT: [
                        CallbackQueryHandler(self.password_callback, pattern='^password_'),
                    ],
                    PASSWORD_INPUT: [
                        MessageHandler(filters.TEXT & ~filters.COMMAND, self.password_input),
                    ],
                    CONFIRM_CREATE: [
                        CallbackQueryHandler(self.confirm_callback, pattern='^confirm_'),
                    ],
                },
                fallbacks=[
                    CommandHandler('cancel', self.cancel_command),
                    CallbackQueryHandler(self.cancel_callback, pattern='^cancel$'),
                ],
            )
            
            logger.info("Adding handlers...")
            application.add_handler(CommandHandler('start', self.start_command))
            application.add_handler(CommandHandler('help', self.help_command))
            application.add_handler(CommandHandler('status', self.status_command))
            application.add_handler(conv_handler)
            
            logger.info("🚀 Bot starting...")
            logger.info("✅ Bot running! Send /start")
            
            application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Failed to run: {e}")
            traceback.print_exc()
            raise


def main():
    """Main entry point."""
    try:
        print("="*60)
        print("Instagram Account Creator Bot")
        print("="*60)
        
        token = os.getenv('TELEGRAM_BOT_TOKEN') or Config.TELEGRAM_BOT_TOKEN
        if not token:
            print("ERROR: No token!")
            sys.exit(1)
        
        try:
            Config.validate()
        except ValueError as e:
            print(f"Config error: {e}")
            sys.exit(1)
        
        print(f"✅ Token: {token[:25]}...")
        
        bot = InstagramBot()
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Fatal: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
