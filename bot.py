"""
Telegram Bot for Instagram Account Creator.
Main bot interface and command handlers.
"""

import logging
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
from typing import Dict, Any
import asyncio

from config import Config
from user_config import UserConfig, UsernameMode, FullNameMode
from password_manager import PasswordMode
from instagram_creator import InstagramCreator
from email_providers import EmailProviderManager
from captcha_solver import CaptchaSolver
from utils import estimate_creation_time, format_time, get_progress_bar

logger = logging.getLogger(__name__)

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
        self.user_configs: Dict[int, UserConfig] = {}
        self.email_manager = EmailProviderManager()
        self.captcha_solver = CaptchaSolver()
        
        logger.info("InstagramBot initialized")
    
    def get_user_config(self, user_id: int) -> UserConfig:
        """Get or create user configuration."""
        if user_id not in self.user_configs:
            self.user_configs[user_id] = UserConfig()
        return self.user_configs[user_id]
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        welcome_text = (
            "🎉 <b>Welcome to Instagram Account Creator Bot!</b>\n\n"
            "This bot helps you create Instagram accounts automatically.\n\n"
            "<b>Features:</b>\n"
            "✨ Create 1-50 accounts at once\n"
            "🔐 Custom or random passwords\n"
            "👤 Flexible username options\n"
            "📧 12 reliable email providers\n"
            "🤖 Smart captcha solving\n"
            "📊 Real-time progress updates\n\n"
            "<b>Commands:</b>\n"
            "/create - Start creating accounts\n"
            "/status - Check system status\n"
            "/balance - Check captcha balance\n"
            "/help - Get help\n"
            "/cancel - Cancel operation\n\n"
            "Click /create to get started!"
        )
        
        await update.message.reply_text(welcome_text, parse_mode='HTML')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_text = (
            "📖 <b>Help Guide</b>\n\n"
            "<b>How to use:</b>\n"
            "1. Use /create to start the wizard\n"
            "2. Choose number of accounts (1-50)\n"
            "3. Configure username generation\n"
            "4. Configure full name\n"
            "5. Choose password mode\n"
            "6. Confirm and start creation\n\n"
            "<b>Username Modes:</b>\n"
            "• Random: Generates random usernames\n"
            "• Prefix: Uses your custom prefix\n"
            "• List: Use your own username list\n\n"
            "<b>Password Modes:</b>\n"
            "• Custom: Same password for all accounts\n"
            "• Random: Unique password for each account\n\n"
            "<b>Tips:</b>\n"
            "💡 Use Tier 1 email providers for best results\n"
            "💡 Start with 1-5 accounts to test\n"
            "💡 Random passwords are more secure\n\n"
            "Need more help? Contact support!"
        )
        
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command."""
        status_text = "📊 <b>System Status</b>\n\n"
        status_text += self.email_manager.get_provider_status()
        
        await update.message.reply_text(status_text, parse_mode='HTML')
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /balance command."""
        balance = self.captcha_solver.get_balance_str()
        
        balance_text = (
            f"💰 <b>Captcha Balance</b>\n\n"
            f"2Captcha: {balance}\n\n"
        )
        
        if Config.CAPTCHA_API_KEY:
            balance_text += "✅ API Key configured"
        else:
            balance_text += "⚠️ No API key configured\n(Free methods only)"
        
        await update.message.reply_text(balance_text, parse_mode='HTML')
    
    async def create_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /create command - start creation wizard."""
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
            "🔢 <b>How many accounts do you want to create?</b>\n\n"
            "Select a quick option or choose custom (1-50):"
        )
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return QUANTITY_SELECT
    
    async def quantity_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle quantity selection."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_config = self.get_user_config(user_id)
        
        data = query.data
        
        if data == "qty_custom":
            await query.edit_message_text(
                "🔢 Enter the number of accounts (1-50):",
                parse_mode='HTML'
            )
            return QUANTITY_SELECT
        
        elif data.startswith("qty_"):
            num = int(data.split("_")[1])
            user_config.set_account_quantity(num)
            
            estimated_time = estimate_creation_time(num)
            
            keyboard = [
                [
                    InlineKeyboardButton("Fully Random", callback_data="username_random"),
                ],
                [
                    InlineKeyboardButton("Custom Prefix", callback_data="username_prefix"),
                ],
                [
                    InlineKeyboardButton("Custom List", callback_data="username_list"),
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = (
                f"✅ Creating <b>{num}</b> accounts\n"
                f"⏱ Estimated time: {format_time(estimated_time)}\n\n"
                "👤 <b>Choose username mode:</b>\n\n"
                "• <b>Fully Random:</b> alex_8492, jordan_7281\n"
                "• <b>Custom Prefix:</b> mybrand_8492, mybrand_7281\n"
                "• <b>Custom List:</b> Your own usernames"
            )
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
            return USERNAME_SELECT
    
    async def quantity_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle custom quantity input."""
        try:
            num = int(update.message.text)
            
            if num < 1 or num > 50:
                await update.message.reply_text("❌ Please enter a number between 1 and 50.")
                return QUANTITY_SELECT
            
            user_id = update.message.from_user.id
            user_config = self.get_user_config(user_id)
            user_config.set_account_quantity(num)
            
            estimated_time = estimate_creation_time(num)
            
            keyboard = [
                [
                    InlineKeyboardButton("Fully Random", callback_data="username_random"),
                ],
                [
                    InlineKeyboardButton("Custom Prefix", callback_data="username_prefix"),
                ],
                [
                    InlineKeyboardButton("Custom List", callback_data="username_list"),
                ],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = (
                f"✅ Creating <b>{num}</b> accounts\n"
                f"⏱ Estimated time: {format_time(estimated_time)}\n\n"
                "👤 <b>Choose username mode:</b>\n\n"
                "• <b>Fully Random:</b> alex_8492, jordan_7281\n"
                "• <b>Custom Prefix:</b> mybrand_8492, mybrand_7281\n"
                "• <b>Custom List:</b> Your own usernames"
            )
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
            return USERNAME_SELECT
            
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number.")
            return QUANTITY_SELECT
    
    async def username_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle username mode selection."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_config = self.get_user_config(user_id)
        
        data = query.data
        
        if data == "username_random":
            user_config.set_username_mode(UsernameMode.RANDOM)
            return await self._show_fullname_menu(query, user_config)
        
        elif data == "username_prefix":
            await query.edit_message_text(
                "📝 Enter your custom prefix:\n\n"
                "Example: mybrand\n"
                "Result: mybrand_8492, mybrand_7281, etc.",
                parse_mode='HTML'
            )
            context.user_data['username_mode'] = 'prefix'
            return USERNAME_INPUT
        
        elif data == "username_list":
            await query.edit_message_text(
                f"📝 Send {user_config.num_accounts} usernames (one per line):\n\n"
                "Example:\n"
                "cooluser1\n"
                "awesomeguy2\n"
                "bestaccount3",
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
            await update.message.reply_text(f"✅ Prefix set: {prefix}")
            
        elif mode == 'list':
            usernames = [line.strip() for line in update.message.text.split('\n') if line.strip()]
            
            if len(usernames) < user_config.num_accounts:
                await update.message.reply_text(
                    f"❌ You need {user_config.num_accounts} usernames, but only provided {len(usernames)}.\n"
                    "Please send again:"
                )
                return USERNAME_INPUT
            
            user_config.set_username_mode(UsernameMode.LIST, custom_list=usernames)
            await update.message.reply_text(f"✅ {len(usernames)} usernames saved")
        
        return await self._show_fullname_menu_message(update, user_config)
    
    async def _show_fullname_menu(self, query, user_config) -> int:
        """Show fullname selection menu."""
        keyboard = [
            [InlineKeyboardButton("Random Names", callback_data="fullname_random")],
            [InlineKeyboardButton("Same Name for All", callback_data="fullname_same")],
            [InlineKeyboardButton("Custom List", callback_data="fullname_list")],
            [InlineKeyboardButton("Empty (No Name)", callback_data="fullname_empty")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "📝 <b>Choose full name mode:</b>\n\n"
            "• <b>Random:</b> Bot picks realistic names\n"
            "• <b>Same:</b> One name for all accounts\n"
            "• <b>List:</b> Your own list of names\n"
            "• <b>Empty:</b> Leave name blank"
        )
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return FULLNAME_SELECT
    
    async def _show_fullname_menu_message(self, update, user_config) -> int:
        """Show fullname selection menu (message version)."""
        keyboard = [
            [InlineKeyboardButton("Random Names", callback_data="fullname_random")],
            [InlineKeyboardButton("Same Name for All", callback_data="fullname_same")],
            [InlineKeyboardButton("Custom List", callback_data="fullname_list")],
            [InlineKeyboardButton("Empty (No Name)", callback_data="fullname_empty")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "📝 <b>Choose full name mode:</b>\n\n"
            "• <b>Random:</b> Bot picks realistic names\n"
            "• <b>Same:</b> One name for all accounts\n"
            "• <b>List:</b> Your own list of names\n"
            "• <b>Empty:</b> Leave name blank"
        )
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return FULLNAME_SELECT
    
    async def fullname_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle fullname mode selection."""
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
            await query.edit_message_text(
                "📝 Enter the full name to use for all accounts:\n\n"
                "Example: John Smith",
                parse_mode='HTML'
            )
            context.user_data['fullname_mode'] = 'same'
            return FULLNAME_INPUT
        
        elif data == "fullname_list":
            await query.edit_message_text(
                f"📝 Send {user_config.num_accounts} full names (one per line):\n\n"
                "Example:\n"
                "John Smith\n"
                "Jane Doe\n"
                "Bob Johnson",
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
            await update.message.reply_text(f"✅ Name set: {name}")
            
        elif mode == 'list':
            names = [line.strip() for line in update.message.text.split('\n') if line.strip()]
            
            if len(names) < user_config.num_accounts:
                await update.message.reply_text(
                    f"❌ You need {user_config.num_accounts} names, but only provided {len(names)}.\n"
                    "Please send again:"
                )
                return FULLNAME_INPUT
            
            user_config.set_fullname_mode(FullNameMode.LIST, custom_list=names)
            await update.message.reply_text(f"✅ {len(names)} names saved")
        
        return await self._show_password_menu_message(update, user_config)
    
    async def _show_password_menu(self, query, user_config) -> int:
        """Show password selection menu."""
        keyboard = [
            [InlineKeyboardButton("🔒 Custom Password (Same for All)", callback_data="password_custom")],
            [InlineKeyboardButton("🎲 Random Passwords (Unique Each)", callback_data="password_random")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "🔐 <b>Choose password mode:</b>\n\n"
            "• <b>Custom:</b> You provide ONE password\n"
            "  → All accounts use the SAME password\n"
            "  → Easy to remember\n\n"
            "• <b>Random:</b> Bot generates passwords\n"
            "  → Each account gets UNIQUE password\n"
            "  → More secure\n"
            "  → 12 characters with letters, numbers, symbols"
        )
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return PASSWORD_SELECT
    
    async def _show_password_menu_message(self, update, user_config) -> int:
        """Show password selection menu (message version)."""
        keyboard = [
            [InlineKeyboardButton("🔒 Custom Password (Same for All)", callback_data="password_custom")],
            [InlineKeyboardButton("🎲 Random Passwords (Unique Each)", callback_data="password_random")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "🔐 <b>Choose password mode:</b>\n\n"
            "• <b>Custom:</b> You provide ONE password\n"
            "  → All accounts use the SAME password\n"
            "  → Easy to remember\n\n"
            "• <b>Random:</b> Bot generates passwords\n"
            "  → Each account gets UNIQUE password\n"
            "  → More secure\n"
            "  → 12 characters with letters, numbers, symbols"
        )
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return PASSWORD_SELECT
    
    async def password_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle password mode selection."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_config = self.get_user_config(user_id)
        
        data = query.data
        
        if data == "password_random":
            user_config.set_password_config(PasswordMode.RANDOM)
            return await self._show_confirmation(query, user_config)
        
        elif data == "password_custom":
            await query.edit_message_text(
                "🔒 Enter your password:\n\n"
                "Requirements:\n"
                "• At least 6 characters\n"
                "• This password will be used for ALL accounts\n\n"
                "Send your password:",
                parse_mode='HTML'
            )
            return PASSWORD_INPUT
    
    async def password_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle password input."""
        user_id = update.message.from_user.id
        user_config = self.get_user_config(user_id)
        password = update.message.text
        
        # Validate password
        is_valid, error = user_config.password_manager.validate_password(password)
        
        if not is_valid:
            await update.message.reply_text(f"❌ {error}\n\nPlease try again:")
            return PASSWORD_INPUT
        
        user_config.set_password_config(PasswordMode.CUSTOM, custom_password=password)
        
        # Delete user's password message for security
        try:
            await update.message.delete()
        except:
            pass
        
        await update.message.reply_text("✅ Password set successfully!")
        
        return await self._show_confirmation_message(update, user_config)
    
    async def _show_confirmation(self, query, user_config) -> int:
        """Show configuration confirmation."""
        summary = user_config.get_summary()
        
        keyboard = [
            [InlineKeyboardButton("✅ Start Creating", callback_data="confirm_yes")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"{summary}\n\n<b>Ready to start?</b>"
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return CONFIRM_CREATE
    
    async def _show_confirmation_message(self, update, user_config) -> int:
        """Show configuration confirmation (message version)."""
        summary = user_config.get_summary()
        
        keyboard = [
            [InlineKeyboardButton("✅ Start Creating", callback_data="confirm_yes")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"{summary}\n\n<b>Ready to start?</b>"
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        return CONFIRM_CREATE
    
    async def confirm_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle confirmation."""
        query = update.callback_query
        await query.answer()
        
        if query.data == "confirm_yes":
            user_id = query.from_user.id
            user_config = self.get_user_config(user_id)
            
            await query.edit_message_text("🚀 Starting account creation...\n\nPlease wait...")
            
            # Start account creation
            await self._create_accounts(query, user_config)
            
            return ConversationHandler.END
        
        return ConversationHandler.END
    
    async def _create_accounts(self, query, user_config: UserConfig) -> None:
        """Create accounts and send progress updates."""
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
        
        # Create accounts
        creator = InstagramCreator(user_config, progress_callback)
        
        try:
            summary = await asyncio.to_thread(creator.create_accounts)
            
            # Send final summary
            result_text = (
                "✨ <b>Account Creation Complete!</b>\n\n"
                f"✅ Successful: {summary['successful']}\n"
                f"❌ Failed: {summary['failed']}\n"
                f"⏱ Time: {format_time(summary['elapsed_time'])}\n\n"
            )
            
            if summary['successful'] > 0:
                result_text += "<b>Created Accounts:</b>\n"
                for acc in summary['accounts'][:5]:  # Show first 5
                    result_text += f"• @{acc['username']}\n"
                
                if len(summary['accounts']) > 5:
                    result_text += f"... and {len(summary['accounts']) - 5} more\n"
                
                result_text += f"\n💾 Credentials saved to {Config.CREDENTIALS_FILE}"
            
            await query.message.reply_text(result_text, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error in account creation: {e}")
            await query.message.reply_text(
                f"❌ Error during account creation:\n{str(e)}",
                parse_mode='HTML'
            )
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /cancel command."""
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END
    
    async def cancel_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle cancel button."""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ Operation cancelled.")
        return ConversationHandler.END
    
    def run(self):
        """Run the bot."""
        # Create application
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Create conversation handler
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
        
        # Add handlers
        application.add_handler(CommandHandler('start', self.start_command))
        application.add_handler(CommandHandler('help', self.help_command))
        application.add_handler(CommandHandler('status', self.status_command))
        application.add_handler(CommandHandler('balance', self.balance_command))
        application.add_handler(conv_handler)
        
        # Run bot
        logger.info("Bot starting...")
        application.run_polling()


if __name__ == '__main__':
    bot = InstagramBot()
    bot.run()
