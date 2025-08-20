from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from config import (
    COMPROBANTE1_CONFIG,
    COMPROBANTE4_CONFIG,
    COMPROBANTE_MOVIMIENTO_CONFIG,
    COMPROBANTE_MOVIMIENTO2_CONFIG,
    COMPROBANTE_QR_CONFIG,
)
from utils import generar_comprobante
from auth_system import AuthSystem
import os

# Configuration
ADMIN_ID = 8113919663
ALLOWED_GROUP = -1002726127020

# Initialize authorization system
auth_system = AuthSystem(ADMIN_ID, ALLOWED_GROUP)

user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Check authorization
    if not auth_system.can_use_bot(user_id, chat_id):
        await update.message.reply_text("❌ No tienes permiso para usar este bot.")
        return

    # Botones en 2 filas
    keyboard = [
        [
            InlineKeyboardButton("📝 nequi", callback_data="comprobante1"),
            InlineKeyboardButton("📄 transfiya", callback_data="comprobante4"),
        ],
        [
            InlineKeyboardButton("🤖 comprobante QR", callback_data="comprobante_qr"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Generador de comprobantes nequi totalmente gratis. "
        "Si te lo vendieron, fuiste estafado. Owner @Sangre_binerojs",
        reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat.id

       # Si query.data es None, usar clave por defecto
    tipo = query.data or "default"

    user_data_store[user_id] = {"step": 0, "tipo": tipo}

    prompts = {
        "comprobante1": "👤 Ingresa el nombre:",
        "comprobante4": "📞 Digite el número de teléfono:",
        "movimiento": "👤 Ingresa el nombre:",
        "movimiento2": "👤 Ingresa el nombre:",
        "comprobante_qr": "🏪 Escribe el nombre del negocio:",
    }

    # Siempre pasa un str válido a .get()
    await query.message.reply_text(prompts.get(tipo, "🔍 Inicia ingresando los datos:"))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    # Authorization check
    if not auth_system.can_use_bot(user_id, chat_id):
        return

    if user_id not in user_data_store:
        return

    data = user_data_store[user_id]
    tipo = data["tipo"]
    step = data["step"]

    # --- NEQUI ---
    if tipo == "comprobante1":
        if step == 0:
            data["nombre"] = text
            data["step"] = 1
            await update.message.reply_text("📞 Ingresa el número de teléfono:")
        elif step == 1:
            data["telefono"] = text
            data["step"] = 2
            await update.message.reply_text("💰 Ingresa el valor:")
        elif step == 2:
            if not text.replace("-", "", 1).isdigit():
                await update.message.reply_text("⚠️ El valor debe ser numérico.")
                return
            data["valor"] = int(text)
            output_path = generar_comprobante(data, COMPROBANTE1_CONFIG)
            with open(output_path, "rb") as f:
                await update.message.reply_document(document=f, caption="✅ owner @Sangre_binerojs.")
            os.remove(output_path)

            # movimiento negativo
            data_mov = data.copy()
            data_mov["nombre"] = data["nombre"].upper()
            data_mov["valor"] = -abs(data["valor"])
            output_path_mov = generar_comprobante(data_mov, COMPROBANTE_MOVIMIENTO_CONFIG)
            with open(output_path_mov, "rb") as f:
                await update.message.reply_document(document=f, caption="📄 bot gratis.")
            os.remove(output_path_mov)

            del user_data_store[user_id]

    # --- TRANSFIYA ---
    elif tipo == "comprobante4":
        if step == 0:
            data["telefono"] = text
            data["step"] = 1
            await update.message.reply_text("💸 Digite el valor:")
        elif step == 1:
            if not text.replace("-", "", 1).isdigit():
                await update.message.reply_text("⚠️ El valor debe ser numérico.")
                return
            data["valor"] = int(text)
            output_path = generar_comprobante(data, COMPROBANTE4_CONFIG)
            with open(output_path, "rb") as f:
                await update.message.reply_document(document=f, caption="✅ owner @Sangre_binerojs.")
            os.remove(output_path)

            # movimiento negativo
            data_mov2 = {
                "telefono": data["telefono"],
                "valor": -abs(data["valor"]),
                "nombre": data["telefono"],
            }
            output_path_mov2 = generar_comprobante(data_mov2, COMPROBANTE_MOVIMIENTO2_CONFIG)
            with open(output_path_mov2, "rb") as f:
                await update.message.reply_document(document=f, caption="📄 bot gratis.")
            os.remove(output_path_mov2)

            del user_data_store[user_id]

    # --- MOVIMIENTOS ---
    elif tipo in ["movimiento", "movimiento2"]:
        if step == 0:
            data["nombre"] = text
            data["step"] = 1
            await update.message.reply_text("💰 Ingresa el valor:")
        elif step == 1:
            if not text.isdigit():
                await update.message.reply_text("⚠️ El valor debe ser numérico.")
                return
            data["valor"] = int(text)

            cfg = COMPROBANTE_MOVIMIENTO_CONFIG if tipo == "movimiento" else COMPROBANTE_MOVIMIENTO2_CONFIG
            output_path = generar_comprobante(data, cfg)
            with open(output_path, "rb") as f:
                await update.message.reply_document(document=f, caption="✅ owner @Sangre_binerojs.")
            os.remove(output_path)

            del user_data_store[user_id]

    # --- NUEVO: COMPROBANTE QR ---
    elif tipo == "comprobante_qr":
        if step == 0:
            data["nombre"] = text
            data["step"] = 1
            await update.message.reply_text("💸 Ingresa el valor:")
        elif step == 1:
            if not text.replace("-", "", 1).isdigit():
                await update.message.reply_text("⚠️ El valor debe ser numérico.")
                return
            data["valor"] = int(text)

            output_path = generar_comprobante(data, COMPROBANTE_QR_CONFIG)
            with open(output_path, "rb") as f:
                await update.message.reply_document(document=f, caption="✅ comprobante QR generado.")
            os.remove(output_path)

            # Movimiento adicional con plantilla 3
            data_mov_qr = {
                "nombre": data["nombre"].upper(),
                "valor": -abs(data["valor"])
            }
            from config import COMPROBANTE_MOVIMIENTO3_CONFIG
            output_path_movqr = generar_comprobante(data_mov_qr, COMPROBANTE_MOVIMIENTO3_CONFIG)
            with open(output_path_movqr, "rb") as f:
                await update.message.reply_document(document=f, caption="📄 movimiento QR generado.")
            os.remove(output_path_movqr)
            with open(output_path, "rb") as f:
                await update.message.reply_document(document=f, caption="✅ owner @Sangre_binerojs.")
            os.remove(output_path)

            del user_data_store[user_id]

# Admin Commands
async def gratis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable gratis mode - all users can use the bot"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Check if admin and in allowed group
    if not auth_system.is_admin(user_id):
        await update.message.reply_text("❌ Solo el administrador puede usar este comando.")
        return
    
    if chat_id != ALLOWED_GROUP:
        await update.message.reply_text("❌ Este comando solo funciona en el grupo autorizado.")
        return
    
    auth_system.set_gratis_mode(True)
    await update.message.reply_text("✅ Modo GRATIS activado. Todos los usuarios pueden usar el bot.")

async def off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Disable gratis mode - only authorized users can use the bot"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Check if admin and in allowed group
    if not auth_system.is_admin(user_id):
        await update.message.reply_text("❌ Solo el administrador puede usar este comando.")
        return
    
    if chat_id != ALLOWED_GROUP:
        await update.message.reply_text("❌ Este comando solo funciona en el grupo autorizado.")
        return
    
    auth_system.set_gratis_mode(False)
    await update.message.reply_text("✅ Modo OFF activado. Solo usuarios autorizados pueden usar el bot.")

async def agregar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add user to authorized list"""
    user_id = update.effective_user.id
    
    # Check if admin
    if not auth_system.is_admin(user_id):
        await update.message.reply_text("❌ Solo el administrador puede usar este comando.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Uso: /agregar <id_usuario>")
        return
    
    try:
        target_user_id = int(context.args[0])
        auth_system.add_user(target_user_id)
        await update.message.reply_text(f"✅ Usuario {target_user_id} autorizado.")
    except ValueError:
        await update.message.reply_text("❌ ID de usuario inválido.")

async def eliminar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove user from authorized list"""
    user_id = update.effective_user.id
    
    # Check if admin
    if not auth_system.is_admin(user_id):
        await update.message.reply_text("❌ Solo el administrador puede usar este comando.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Uso: /eliminar <id_usuario>")
        return
    
    try:
        target_user_id = int(context.args[0])
        if auth_system.remove_user(target_user_id):
            await update.message.reply_text(f"✅ Usuario {target_user_id} desautorizado.")
        else:
            await update.message.reply_text(f"⚠️ Usuario {target_user_id} no estaba autorizado.")
    except ValueError:
        await update.message.reply_text("❌ ID de usuario inválido.")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show authorization statistics"""
    user_id = update.effective_user.id
    
    # Check if admin
    if not auth_system.is_admin(user_id):
        await update.message.reply_text("❌ Solo el administrador puede usar este comando.")
        return
    
    stats = auth_system.get_stats()
    authorized_users = auth_system.get_authorized_users()
    
    message = f"📊 **Estadísticas del Bot**\n\n"
    message += f"👥 Usuarios autorizados: {stats['total_authorized']}\n"
    message += f"🆓 Modo gratis: {'Activado' if stats['gratis_mode'] else 'Desactivado'}\n"
    message += f"📱 Grupo permitido: {stats['allowed_group']}\n\n"
    
    if authorized_users:
        message += "👤 Usuarios autorizados:\n"
        for uid in authorized_users:
            message += f"  • {uid}\n"
    else:
        message += "❌ No hay usuarios autorizados."
    
    await update.message.reply_text(message)

def main():
    app = Application.builder().token("TOKEN_AQUI").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gratis", gratis_command))
    app.add_handler(CommandHandler("off", off_command))
    app.add_handler(CommandHandler("agregar", agregar_command))
    app.add_handler(CommandHandler("eliminar", eliminar_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
