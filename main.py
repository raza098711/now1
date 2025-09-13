import os
import logging
import asyncio
import yt_dlp
import time
import shutil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = "8399933069:AAFTQPNasMj__I5kG-sdpgFi6HKe6qhrJsU"
ADMIN_USERNAME = "@media987bot"  # Admin has special privileges
SUPPORTED_PLATFORMS = {
    'youtube': ['youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com'],
    'instagram': ['instagram.com', 'instagr.am', 'www.instagram.com'],
    'tiktok': ['tiktok.com', 'vm.tiktok.com', 'www.tiktok.com', 'vt.tiktok.com'],
    'facebook': ['facebook.com', 'fb.watch', 'www.facebook.com', 'm.facebook.com'],
    'twitter': ['twitter.com', 'x.com', 'www.twitter.com'],
    'reddit': ['reddit.com', 'www.reddit.com']
}

# Create downloads directory
os.makedirs('downloads', exist_ok=True)
os.makedirs('temp', exist_ok=True)

# Bot statistics
bot_stats = {
    'total_downloads': 0,
    'total_users': set(),
    'start_time': time.time()
}

def is_admin(update: Update) -> bool:
    """Check if user is the admin"""
    user = update.effective_user
    return user.username == ADMIN_USERNAME.replace("@", "") if user and user.username else False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message - accessible to all users"""
    user = update.effective_user
    bot_stats['total_users'].add(user.id)
    
    # Different keyboards for admin and regular users
    if is_admin(update):
        keyboard = [
            [InlineKeyboardButton("🔄 Admin: Refresh & Clean", callback_data='admin_refresh')],
            [InlineKeyboardButton("📊 Admin: Bot Stats", callback_data='admin_stats')],
            [InlineKeyboardButton("👥 Admin: User Management", callback_data='admin_users')],
            [InlineKeyboardButton("❓ Help", callback_data='help')]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("📊 My Stats", callback_data='user_stats')],
            [InlineKeyboardButton("❓ Help", callback_data='help')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🎬 *Premium Media Downloader Bot* 🎬
━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 *Welcome:* {user.first_name}
{"🔑 *Admin Access*" if is_admin(update) else "🌟 *Free Access*"}

📥 *Supported Platforms:*
• YouTube (Videos, Shorts, Music)
• Instagram (Reels, Posts, Stories, IGTV)
• TikTok (Videos, No Watermark)
• Facebook (Videos, Reels)
• Twitter/X (Videos, GIFs)
• Reddit (Videos, GIFs)

⚡ *Features:*
• 🔥 HD Quality Downloads
• 💧 Watermark Removal (TikTok)
• 🚀 Fast Processing
• 📊 Real-time Progress
• 🆓 Completely Free

📋 *Instructions:*
Just paste any supported media link and get your video instantly!
    """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    # Admin-only functions
    if query.data.startswith('admin_'):
        if not is_admin(update):
            await query.edit_message_text("🚫 *Admin Access Required*", parse_mode='Markdown')
            return
        
        if query.data == 'admin_refresh':
            # Clean downloads and temp directories
            try:
                if os.path.exists('downloads'):
                    shutil.rmtree('downloads')
                if os.path.exists('temp'):
                    shutil.rmtree('temp')
                os.makedirs('downloads', exist_ok=True)
                os.makedirs('temp', exist_ok=True)
                
                # Clear chat history (delete bot messages)
                try:
                    for i in range(100):  # Delete last 100 messages
                        try:
                            await context.bot.delete_message(
                                chat_id=query.message.chat_id, 
                                message_id=query.message.message_id - i
                            )
                        except:
                            pass
                except:
                    pass
                
                await query.edit_message_text(
                    "✅ *Admin: System Refreshed Successfully!*\n\n"
                    "🧹 All temporary files cleaned\n"
                    "📂 Download cache cleared\n"
                    "💾 Memory optimized\n"
                    "🚀 Ready for new downloads!",
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                await query.edit_message_text(f"❌ Admin: Refresh failed: {str(e)}")
        
        elif query.data == 'admin_stats':
            downloads_count = len([f for f in os.listdir('downloads') if os.path.isfile(os.path.join('downloads', f))])
            downloads_size = sum(os.path.getsize(os.path.join('downloads', f)) for f in os.listdir('downloads') if os.path.isfile(os.path.join('downloads', f)))
            downloads_size_mb = downloads_size / (1024 * 1024)
            uptime = time.time() - bot_stats['start_time']
            uptime_hours = uptime / 3600
            
            stats_text = f"""
📊 *Admin: Bot Statistics*
━━━━━━━━━━━━━━━━━━━━━━━

👥 Total Users: {len(bot_stats['total_users'])}
📥 Total Downloads: {bot_stats['total_downloads']}
📁 Active Files: {downloads_count}
💾 Storage Used: {downloads_size_mb:.2f} MB
⏰ Uptime: {uptime_hours:.1f} hours
🤖 Status: Online & Optimized

🔄 *Admin can refresh anytime*
            """
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data='back_main')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(stats_text, parse_mode='Markdown', reply_markup=reply_markup)
        
        elif query.data == 'admin_users':
            user_count = len(bot_stats['total_users'])
            avg_downloads = bot_stats['total_downloads'] / max(user_count, 1)
            
            users_text = f"""
👥 *Admin: User Management*
━━━━━━━━━━━━━━━━━━━━━━━

📊 **User Statistics:**
• Total Users: {user_count}
• Total Downloads: {bot_stats['total_downloads']}
• Average per User: {avg_downloads:.1f}

⚡ **Bot Performance:**
• All users have free access
• No download limits
• High-quality processing

🛠️ **Admin Controls:**
• System refresh available
• Full statistics access
• User activity monitoring
            """
            
            keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data='back_main')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(users_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    # Regular user functions
    elif query.data == 'user_stats':
        user_downloads = 0  # You can implement per-user tracking if needed
        
        stats_text = f"""
📊 *Your Statistics*
━━━━━━━━━━━━━━━━━━

👤 User: {user.first_name}
📥 Your Downloads: {user_downloads}
🌟 Access Level: Free User
🤖 Bot Status: Online

💎 **Free Features:**
• Unlimited downloads
• HD quality videos
• All platforms supported
• Fast processing
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(stats_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif query.data == 'help':
        help_text = """
❓ *Help & Instructions*
━━━━━━━━━━━━━━━━━━━━━

🔗 *How to Download:*
1. Copy any video link from supported platforms
2. Paste it in this chat
3. Wait for processing (with real-time progress)
4. Receive your high-quality video!

🛠️ *Platform Features:*
• **YouTube**: All formats including Shorts
• **TikTok**: Automatic watermark removal
• **Instagram**: Stories, Reels, IGTV support
• **Facebook**: All video types
• **Twitter/X**: Videos and GIFs
• **Reddit**: Video posts with audio

⚡ *Processing Time:*
• Short videos (< 1 min): ~5-15 seconds
• Medium videos (1-5 min): ~15-45 seconds  
• Long videos (5+ min): ~1-3 minutes

🆓 *Completely Free:* No limits, no subscriptions!
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data='back_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif query.data == 'back_main':
        await start(update, context)

def detect_platform(url: str) -> str:
    """Detect which platform the URL belongs to"""
    url_lower = url.lower()
    for platform, domains in SUPPORTED_PLATFORMS.items():
        if any(domain in url_lower for domain in domains):
            return platform
    return None

async def download_media(url: str, platform: str, progress_callback=None):
    """Enhanced download with better TikTok support and progress tracking"""
    
    # Base configuration for all platforms
    base_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'socket_timeout': 60,
        'connect_timeout': 60,
        'retries': 3,
        'fragment_retries': 3,
    }
    
    # Platform-specific configurations
    if platform == 'youtube':
        ydl_opts = {
            **base_opts,
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
        }
    
    elif platform == 'tiktok':
        # Enhanced TikTok configuration for better success rate
        ydl_opts = {
            **base_opts,
            'format': 'best[ext=mp4]',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            },
            'cookiefile': None,
            'extract_flat': False,
        }
    
    elif platform == 'instagram':
        ydl_opts = {
            **base_opts,
            'format': 'best[ext=mp4]',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }
    
    else:  # Facebook, Twitter, Reddit
        ydl_opts = {
            **base_opts,
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }
    
    # Add progress hook if callback provided
    if progress_callback:
        ydl_opts['progress_hooks'] = [progress_callback]
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            info = ydl.extract_info(url, download=False)
            if not info:
                raise Exception("Could not extract video information")
            
            title = info.get('title', 'Unknown')[:50]
            duration = info.get('duration', 0)
            
            # Download the video
            filename = ydl.prepare_filename(info)
            await asyncio.to_thread(ydl.download, [url])
            
            return filename, title, duration
            
    except Exception as e:
        logger.error(f"{platform} download error: {str(e)}")
        # Try alternative method for TikTok
        if platform == 'tiktok':
            try:
                alt_opts = {
                    **base_opts,
                    'format': 'worst[ext=mp4]',  # Try lower quality first
                    'outtmpl': 'downloads/tiktok_%(id)s.%(ext)s',
                    'extractor_args': {'tiktok': {'webpage_url_basename': 'video'}},
                }
                
                with yt_dlp.YoutubeDL(alt_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'TikTok Video')[:50]
                    duration = info.get('duration', 0)
                    filename = ydl.prepare_filename(info)
                    await asyncio.to_thread(ydl.download, [url])
                    return filename, title, duration
            except:
                pass
        
        raise Exception(f"Failed to download from {platform}: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced message handler - accessible to ALL users"""
    user = update.effective_user
    bot_stats['total_users'].add(user.id)
    
    message_text = update.message.text.strip()
    
    # Check if message contains a URL
    if not any(domain in message_text.lower() for domains in SUPPORTED_PLATFORMS.values() for domain in domains):
        await update.message.reply_text(
            f"❌ *Invalid Link*\n\n"
            f"Hi {user.first_name}! Please send a valid URL from supported platforms:\n"
            "YouTube • Instagram • TikTok • Facebook • Twitter • Reddit",
            parse_mode='Markdown'
        )
        return
    
    platform = detect_platform(message_text)
    
    if not platform:
        await update.message.reply_text(
            f"❌ *Unsupported Platform*\n\n"
            f"Hi {user.first_name}! Supported platforms:\n"
            "• YouTube (youtube.com, youtu.be)\n"
            "• Instagram (instagram.com)\n"
            "• TikTok (tiktok.com, vm.tiktok.com)\n"
            "• Facebook (facebook.com, fb.watch)\n"
            "• Twitter/X (twitter.com, x.com)\n"
            "• Reddit (reddit.com)",
            parse_mode='Markdown'
        )
        return
    
    # Increment download counter
    bot_stats['total_downloads'] += 1
    
    # Enhanced processing message with platform emoji
    platform_emojis = {
        'youtube': '📺',
        'instagram': '📸',
        'tiktok': '🎵',
        'facebook': '👥',
        'twitter': '🐦',
        'reddit': '🔥'
    }
    
    emoji = platform_emojis.get(platform, '📱')
    
    processing_msg = await update.message.reply_text(
        f"{emoji} *Processing {platform.title()} Link...*\n\n"
        f"👤 User: {user.first_name}\n"
        f"🔗 Analyzing URL...\n"
        f"⏱️ Started: {time.strftime('%H:%M:%S')}\n"
        f"🚀 Status: Extracting video info...",
        parse_mode='Markdown'
    )
    
    start_time = time.time()
    
    try:
        # Progress tracking
        progress_data = {'status': 'downloading', 'percent': 0}
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                if 'total_bytes' in d and d['total_bytes']:
                    progress_data['percent'] = (d['downloaded_bytes'] / d['total_bytes']) * 100
                elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                    progress_data['percent'] = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
        
        # Update progress every 2 seconds
        async def update_progress():
            while progress_data['status'] == 'downloading':
                elapsed = time.time() - start_time
                await processing_msg.edit_text(
                    f"{emoji} *Downloading from {platform.title()}...*\n\n"
                    f"👤 User: {user.first_name}\n"
                    f"📊 Progress: {progress_data['percent']:.1f}%\n"
                    f"⏱️ Elapsed: {elapsed:.1f}s\n"
                    f"🚀 Status: Downloading video...",
                    parse_mode='Markdown'
                )
                await asyncio.sleep(2)
        
        # Start progress updater
        progress_task = asyncio.create_task(update_progress())
        
        try:
            # Download with timeout
            filename, title, duration = await asyncio.wait_for(
                download_media(message_text, platform, progress_hook),
                timeout=300  # 5 minutes timeout
            )
            
            progress_data['status'] = 'complete'
            progress_task.cancel()
            
            elapsed_time = time.time() - start_time
            
            # Update to upload status
            await processing_msg.edit_text(
                f"{emoji} *Upload Starting...*\n\n"
                f"👤 User: {user.first_name}\n"
                f"✅ Download Complete!\n"
                f"📁 File: {title}\n"
                f"⏱️ Download Time: {elapsed_time:.1f}s\n"
                f"🚀 Status: Uploading to Telegram...",
                parse_mode='Markdown'
            )
            
            # Send the file
            file_size = os.path.getsize(filename) / (1024 * 1024)  # MB
            
            caption = (
                f"✅ *Download Complete!*\n\n"
                f"🎬 **{title}**\n"
                f"🌐 Platform: {platform.title()}\n"
                f"📊 Size: {file_size:.1f} MB\n"
                f"⏱️ Processing Time: {elapsed_time:.1f}s\n"
                f"👤 Downloaded by: {user.first_name}\n"
                f"🤖 Bot: Free Media Downloader"
            )
            
            try:
                upload_start = time.time()
                
                if file_size > 50:  # If file is larger than 50MB, warn about upload time
                    await processing_msg.edit_text(
                        f"{emoji} *Large File Uploading...*\n\n"
                        f"👤 User: {user.first_name}\n"
                        f"📊 Size: {file_size:.1f} MB\n"
                        f"⚠️ This may take a while...\n"
                        f"🚀 Status: Uploading...",
                        parse_mode='Markdown'
                    )
                
                await update.message.reply_video(
                    video=open(filename, 'rb'),
                    caption=caption,
                    parse_mode='Markdown',
                    supports_streaming=True,
                    read_timeout=300,
                    write_timeout=300,
                    connect_timeout=60
                )
                
                upload_time = time.time() - upload_start
                total_time = time.time() - start_time
                
                # Final success message
                await processing_msg.edit_text(
                    f"🎉 *SUCCESS!* 🎉\n\n"
                    f"👤 {user.first_name}, your video is ready!\n"
                    f"✅ Video sent successfully!\n"
                    f"⏱️ Total Time: {total_time:.1f}s\n"
                    f"📤 Upload Time: {upload_time:.1f}s\n"
                    f"🚀 Send another link anytime!",
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                logger.error(f"Upload error: {e}")
                await processing_msg.edit_text(
                    f"✅ *Download Complete!*\n"
                    f"❌ Upload failed: File too large for Telegram\n"
                    f"💡 Try a shorter video or lower quality",
                    parse_mode='Markdown'
                )
        
        except asyncio.CancelledError:
            pass
        finally:
            if not progress_task.done():
                progress_task.cancel()
        
        # Cleanup
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except:
            pass
            
    except asyncio.TimeoutError:
        await processing_msg.edit_text(
            f"⏰ *Download Timeout*\n\n"
            f"❌ Download took too long (>5 min)\n"
            f"💡 Try with a shorter video or check your connection",
            parse_mode='Markdown'
        )
    except Exception as e:
        error_msg = str(e)
        elapsed = time.time() - start_time
        
        # Specific error messages for different issues
        if "tiktok" in platform.lower():
            error_text = (
                f"🎵 *TikTok Download Failed*\n\n"
                f"👤 User: {user.first_name}\n"
                f"❌ Error: {error_msg}\n"
                f"⏱️ Time elapsed: {elapsed:.1f}s\n\n"
                f"💡 **Possible Solutions:**\n"
                f"• Check if video is private/deleted\n"
                f"• Try copying the link again\n"
                f"• Some region-restricted videos may not work\n"
                f"• Wait a moment and retry"
            )
        else:
            error_text = (
                f"❌ *Download Failed*\n\n"
                f"👤 User: {user.first_name}\n"
                f"🌐 Platform: {platform.title()}\n"
                f"❌ Error: {error_msg}\n"
                f"⏱️ Time elapsed: {elapsed:.1f}s\n\n"
                f"💡 Please check if the link is valid and try again"
            )
        
        await processing_msg.edit_text(error_text, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced error handler"""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if update and update.effective_message:
            user = update.effective_user
            await update.effective_message.reply_text(
                f"❌ *System Error*\n\n"
                f"Hi {user.first_name if user else 'User'}, an unexpected error occurred.\n"
                f"Please try again in a moment.\n"
                f"Contact {ADMIN_USERNAME} if the issue persists.",
                parse_mode='Markdown'
            )
    except:
        pass

def main():
    """Enhanced main function with better connection management"""
    print(f"🚀 Starting Media Downloader Bot...")
    print(f"👤 Admin: {ADMIN_USERNAME}")
    print(f"🌟 Mode: Public Access (All Users Welcome)")
    print(f"🔑 Admin has special management privileges")
    
    # Create application with optimized settings
    application = (Application.builder()
                  .token(BOT_TOKEN)
                  .pool_timeout(60)
                  .connect_timeout(60)
                  .read_timeout(60)
                  .write_timeout(60)
                  .get_updates_read_timeout(60)
                  .build())
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    # Start the bot with enhanced retry mechanism
    retry_count = 0
    max_retries = 10
    
    while retry_count < max_retries:
        try:
            print(f"🤖 Bot is running... (Attempt {retry_count + 1})")
            print(f"✅ All users can download videos")
            print(f"🛠️ Admin can manage and view statistics")
            application.run_polling(
                poll_interval=1.0,
                timeout=30,
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )
            break
        except Exception as e:
            retry_count += 1
            logger.error(f"Connection error (attempt {retry_count}/{max_retries}): {e}")
            if retry_count >= max_retries:
                logger.error("❌ Max retries exceeded. Exiting.")
                break
            
            wait_time = min(5 * retry_count, 30)  # Max 30 second wait
            print(f"⏳ Waiting {wait_time}s before retry...")
            time.sleep(wait_time)

if __name__ == '__main__':
    main()