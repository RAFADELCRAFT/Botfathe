import json
import os
import random
from datetime import datetime
from pytz import timezone
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from PIL import Image, ImageDraw, ImageFont

# ================= ESTADOS =================
DESTINATARIO, NUMERO, CANTIDAD = range(3)

# ================= CONFIGURACIÓN =================
ADMIN_ID = 8113919663
USERS_FILE = "users.json"
GROUPS_FILE = "groups.json"
BOT_TOKEN = os.getenv("TOKEN")
FONT_PATH = "manrope_medium.ttf"
IMAGE_PATH = "Comprobantes.jpg"

def load_data(filename):
    try:
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return set(json.load(f))
        return set()
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading {filename}: {e}")
        return set()

def save_data(filename, data_set):
    try:
        with open(filename, "w") as f:
            json.dump(list(data_set), f)
    except IOError as e:
        print(f"Error saving {filename}: {e}")

USERS_ALLOWED = load_data(USERS_FILE)
GROUPS_ALLOWED = load_data(GROUPS_FILE)

# -------- FUNCIONES DE ADMIN --------
async def agregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 No tienes permisos.")
    if not context.args:
        return await update.message.reply_text("❌ Uso: /agregar <id_usuario>")
    try:
        uid = int(context.args[0])
        USERS_ALLOWED.add(uid)
        save_data(USERS_FILE, USERS_ALLOWED)
        await update.message.reply_text(f"✅ Usuario {uid} agregado.")
    except ValueError:
        await update.message.reply_text("❌ El ID debe ser un número entero.")

async def eliminar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 No tienes permisos.")
    if not context.args:
        return await update.message.reply_text("❌ Uso: /eliminar <id_usuario>")
    try:
        uid = int(context.args[0])
        USERS_ALLOWED.discard(uid)
        save_data(USERS_FILE, USERS_ALLOWED)
        await update.message.reply_text(f"❌ Usuario {uid} eliminado.")
    except ValueError:
        await update.message.reply_text("❌ El ID debe ser un número entero.")

async def agregargrupo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 No tienes permisos.")
    gid = update.effective_chat.id
    GROUPS_ALLOWED.add(gid)
    save_data(GROUPS_FILE, GROUPS_ALLOWED)
    await update.message.reply_text(f"✅ Grupo {gid} activado.")

async def eliminargrupo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 No tienes permisos.")
    gid = update.effective_chat.id
    GROUPS_ALLOWED.discard(gid)
    save_data(GROUPS_FILE, GROUPS_ALLOWED)
    await update.message.reply_text(f"❌ Grupo {gid} eliminado.")

async def listado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 No tienes permisos.")
    msg = "📋 *Listado de administración*\n\n"
    msg += f"👤 Usuarios activados: {list(USERS_ALLOWED) if USERS_ALLOWED else 'Ninguno'}\n"
    msg += f"👥 Grupos activados: {list(GROUPS_ALLOWED) if GROUPS_ALLOWED else 'Ninguno'}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

# -------- FUNCIONES PRINCIPALES --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Bienvenido {user.first_name}\n"
        f"🆔 ID: {user.id}\n"
        "👑 Creador: @Sangre_binerojs\n\n"
        "Usa /generar para crear un comprobante si tu cuenta ha sido activada."
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operación cancelada.")
    return ConversationHandler.END

async def generar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if chat.type == "private":
        if user.id not in USERS_ALLOWED:
            return await update.message.reply_text(
                "🚫 Tu cuenta no está activada. Habla con @Sangre_binerojs"
            )
    elif chat.type in ["group", "supergroup"]:
        if chat.id not in GROUPS_ALLOWED:
            return await update.message.reply_text("⚠️ Este grupo no ha sido activado.")

    await update.message.reply_text(
        "✅ *Generando comprobante*\n\n"
        "✍️ Ingresa el *Nombre del Destinatario* (o /cancel para salir):",
        parse_mode="Markdown"
    )
    return DESTINATARIO

async def destinatario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["destinatario"] = update.message.text.strip()
    await update.message.reply_text(
        "📱 Ingresa el *Número de Celular* (10 dígitos y empieza en 3):",
        parse_mode="Markdown"
    )
    return NUMERO

async def numero(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numero = update.message.text.strip()
    if not (len(numero) == 10 and numero.isdigit() and numero.startswith("3")):
        return await update.message.reply_text(
            "❌ Número inválido. Debe tener 10 dígitos y empezar por 3."
        )
    context.user_data["numero"] = numero
    await update.message.reply_text(
        "💰 Ingresa la *Cantidad* (ejemplo 3000):",
        parse_mode="Markdown"
    )
    return CANTIDAD

async def cantidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cantidad = float(update.message.text.strip())  # Permitir decimales
        if cantidad <= 0:
            return await update.message.reply_text("❌ La cantidad debe ser mayor a 0.")
    except ValueError:
        return await update.message.reply_text(
            "❌ Ingresa solo números (ejemplo 3000 o 3000.50)."
        )

    # Formatear cantidad con punto decimal y dos ceros (e.g., 3.000,00)
    formatted = "{:,.2f}".format(cantidad).replace(".", "#").replace(",", ".").replace("#", ",")
    context.user_data["cantidad"] = formatted

    # Fecha actual en Bogotá (UTC-5) con meses en español
    bogota_tz = timezone("America/Bogota")
    bogota_time = datetime.now(bogota_tz)
    meses = {
        'January': 'enero',
        'February': 'febrero',
        'March': 'marzo',
        'April': 'abril',
        'May': 'mayo',
        'June': 'junio',
        'July': 'julio',
        'August': 'agosto',
        'September': 'septiembre',
        'October': 'octubre',
        'November': 'noviembre',
        'December': 'diciembre'
    }
    fecha_str = bogota_time.strftime("%d de %B de %Y a las %I:%M %p").lower()
    for eng, esp in meses.items():
        fecha_str = fecha_str.replace(eng.lower(), esp)
    fecha_str = fecha_str.replace("am", "a.m.").replace("pm", "p.m.")
    context.user_data["fecha"] = fecha_str

    # ======== GENERAR IMAGEN =========
    try:
        img = Image.open(IMAGE_PATH).convert("RGB")  # Asegura que la imagen sea RGB
    except FileNotFoundError:
        await update.message.reply_text(f"❌ Error: No se encontró la imagen {IMAGE_PATH}. Asegúrate de que 'Comprobantes.jpg' esté en el directorio.")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"❌ Error al abrir la imagen: {e}")
        return ConversationHandler.END

    if not os.path.exists(FONT_PATH):
        await update.message.reply_text(
            f"❌ Error: No se encontró la fuente {FONT_PATH} en el directorio {os.getcwd()}. "
            "Asegúrate de que 'manrope_medium.ttf' esté en la misma carpeta que el script."
        )
        return ConversationHandler.END

    try:
        font = ImageFont.truetype(FONT_PATH, 22)
    except OSError as e:
        font = ImageFont.load_default()
        await update.message.reply_text(
            f"❌ Error al cargar la fuente {FONT_PATH}: {e}. Usando fuente predeterminada. "
            "Re-descarga 'manrope_medium.ttf' o usa un archivo .ttf válido."
        )

    draw = ImageDraw.Draw(img)
    # Usar las coordenadas correctas con color #200021
    draw.text((45, 525), context.user_data["destinatario"], font=font, fill="#200021")  # NOMBRE
    draw.text((48, 602), "$" + context.user_data["cantidad"], font=font, fill="#200021")  # CANTIDAD
    draw.text((43, 676), context.user_data["numero"], font=font, fill="#200021")  # NUMERO
    draw.text((45, 747), context.user_data["fecha"], font=font, fill="#200021")  # FECHA
    referencia = "M" + str(random.randint(10000000, 99999999))  # e.g., M20032698
    draw.text((45, 823), referencia, font=font, fill="#200021")  # REFERENCIA

    output = "comprobante_listo.jpg"
    try:
        img.save(output, "JPEG")
        with open(output, "rb") as photo:
            await update.message.reply_photo(photo)
        os.remove(output)
    except (IOError, OSError) as e:
        await update.message.reply_text(f"❌ Error al guardar o enviar la imagen: {e}")
        return ConversationHandler.END

    return ConversationHandler.END

# -------- MAIN --------
def main():
    if not BOT_TOKEN:
        print("Error: No se encontró el token del bot. Configura la variable de entorno TELEGRAM_BOT_TOKEN.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("generar", generar)],
        states={
            DESTINATARIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, destinatario)],
            NUMERO: [MessageHandler(filters.TEXT & ~filters.COMMAND, numero)],
            CANTIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, cantidad)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CommandHandler("agregar", agregar))
    app.add_handler(CommandHandler("eliminar", eliminar))
    app.add_handler(CommandHandler("agregargrupo", agregargrupo))
    app.add_handler(CommandHandler("eliminargrupo", eliminargrupo))
    app.add_handler(CommandHandler("listado", listado))

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
