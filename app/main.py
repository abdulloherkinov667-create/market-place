import os
import django
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from asgiref.sync import sync_to_async

# ================= DJANGO SETUP =================
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from app.models import (
    UzumProduct, Kategoriy, SupportMessage, 
    Users, UzumProductImage, Like, 
    ShopingModel, Order, OrderItem
)

# ================= CONFIG =================
TOKEN = "8664343682:AAHAK6ctV8b-XUcY_T3MDFrNAbxfEjzX8JU"
ADMIN_IDS = [6411347321]

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# ================= STATES =================
class ProductState(StatesGroup):
    name = State()
    category = State()
    price = State()
    about = State()
    images = State()

class SupportState(StatesGroup):
    message = State()

class LoginState(StatesGroup):
    username = State()
    password = State()

# ================= SESSION (xotira) =================
logged_in_users: dict[int, int] = {}

# ================= KEYBOARDS =================
def main_menu(user_id):
    kb = [
        [KeyboardButton(text="📦 Mahsulotlar")],
        [KeyboardButton(text="📩 Shikoyat yuborish")],
        [KeyboardButton(text="📜 Shikoyatlar tarixi")]
    ]
    if user_id in ADMIN_IDS:
        kb.append([KeyboardButton(text="➕ Mahsulot qo'shish")])
        kb.append([KeyboardButton(text="📋 Barcha shikoyatlar")])
    
    # User panel tugmalari
    kb.extend([
        [KeyboardButton(text="❤️ Like'larim"), KeyboardButton(text="🛒 Savatim")],
        [KeyboardButton(text="📦 Buyurtmalarim"), KeyboardButton(text="🌟 Istaklarim")],
        [KeyboardButton(text="📊 Statistikam")],
        [KeyboardButton(text="🚪 Chiqish")]
    ])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def done_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✅ Tugatish")]], resize_keyboard=True)

def main_kb(): # User botdagi original keyboard funksiyasi
    return main_menu(0) 

# ================= HELPERS =================
async def get_logged_user(tg_id: int):
    user_id = logged_in_users.get(tg_id)
    if not user_id:
        return None
    try:
        return await sync_to_async(Users.objects.get)(id=user_id)
    except Users.DoesNotExist:
        logged_in_users.pop(tg_id, None)
        return None

async def require_login(msg: types.Message) -> bool:
    user = await get_logged_user(msg.from_user.id)
    if not user:
        await msg.answer("🔐 Avval tizimga kiring.\n/login buyrug'ini yuboring.")
        return False
    return True

# ╔══════════════════════════════════════════╗
# ║             ADMIN PANEL KODI             ║
# ╚══════════════════════════════════════════╝

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("Xush kelibsiz!", reply_markup=main_menu(msg.from_user.id))

@dp.message(F.text == "📦 Mahsulotlar")
async def products(msg: types.Message):
    all_products = await sync_to_async(list)(UzumProduct.objects.filter(is_active=True))
    if not all_products:
        return await msg.answer("Mahsulot yo'q")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{p.name} - {p.price} so'm", callback_data=f"p_{p.id}")] for p in all_products
    ])
    await msg.answer("📦 Mahsulotlar:", reply_markup=kb)

@dp.callback_query(F.data.startswith("p_"))
async def product_detail(call: types.CallbackQuery):
    pid = int(call.data.split("_")[1])
    try:
        product = await sync_to_async(UzumProduct.objects.get)(id=pid)
    except UzumProduct.DoesNotExist:
        return await call.answer("Mahsulot topilmadi", show_alert=True)
    discount_text = ""
    if product.aksi_narx > 0:
        discounted = int(product.price * (1 - product.aksi_narx / 100))
        discount_text = f"\n🔖 Aksiya: {product.aksi_narx}% → {discounted:,} so'm"
    text = f"📦 *{product.name}*\n💰 {product.price:,} so'm{discount_text}\n\n{product.about}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_products")]])
    images = await sync_to_async(list)(UzumProductImage.objects.filter(product=product))
    if images:
        from django.conf import settings
        image_path = os.path.join(settings.MEDIA_ROOT, str(images[0].image))
        if os.path.exists(image_path):
            await call.message.answer_photo(photo=types.FSInputFile(image_path), caption=text, reply_markup=kb, parse_mode="Markdown")
        else:
            await call.message.answer(text + "\n\n⚠️ Rasm topilmadi", reply_markup=kb, parse_mode="Markdown")
    else:
        await call.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "back_products")
async def back_products(call: types.CallbackQuery):
    await products(call.message)
    await call.answer()

@dp.message(F.text == "➕ Mahsulot qo'shish")
async def add_product(msg: types.Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("❌ Ruxsat yo'q")
    await msg.answer("📝 Mahsulot nomini yozing:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Bekor qilish")]], resize_keyboard=True))
    await state.set_state(ProductState.name)

@dp.message(F.text == "🔙 Bekor qilish")
async def cancel_state(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("❌ Bekor qilindi", reply_markup=main_menu(msg.from_user.id))

@dp.message(ProductState.name)
async def get_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    cats = await sync_to_async(list)(Kategoriy.objects.all())
    if not cats:
        await msg.answer("⚠️ Hech qanday kategoriya yo'q. Avval kategoriya qo'shing.")
        await state.clear()
        return
    kb = [[KeyboardButton(text=c.name)] for c in cats]
    kb.append([KeyboardButton(text="🔙 Bekor qilish")])
    await msg.answer("📂 Kategoriyani tanlang:", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.set_state(ProductState.category)

@dp.message(ProductState.category)
async def get_category(msg: types.Message, state: FSMContext):
    try:
        category = await sync_to_async(Kategoriy.objects.get)(name=msg.text)
    except Kategoriy.DoesNotExist:
        return await msg.answer("❌ Bunday kategoriya yo'q. Ro'yxatdan tanlang.")
    await state.update_data(category_id=category.id)
    await msg.answer("💰 Narxni kiriting:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Bekor qilish")]], resize_keyboard=True))
    await state.set_state(ProductState.price)

@dp.message(ProductState.price)
async def get_price(msg: types.Message, state: FSMContext):
    if not msg.text.isdigit():
        return await msg.answer("❌ Faqat son kiriting!")
    await state.update_data(price=int(msg.text))
    await msg.answer("📄 Mahsulot haqida ma'lumot yozing:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Bekor qilish")]], resize_keyboard=True))
    await state.set_state(ProductState.about)

@dp.message(ProductState.about)
async def get_about(msg: types.Message, state: FSMContext):
    await state.update_data(about=msg.text, images=[])
    await msg.answer("🖼 Rasmlarni yuboring:", reply_markup=done_keyboard())
    await state.set_state(ProductState.images)

@dp.message(ProductState.images, F.photo)
async def get_images(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    images = data.get("images", [])
    file = await bot.get_file(msg.photo[-1].file_id)
    downloaded = await bot.download_file(file.file_path)
    from django.conf import settings
    save_dir = os.path.join(settings.MEDIA_ROOT, "maxsulot_rasm")
    os.makedirs(save_dir, exist_ok=True)
    filename = f"{msg.photo[-1].file_id}.jpg"
    full_path = os.path.join(save_dir, filename)
    with open(full_path, "wb") as f:
        f.write(downloaded.read())
    images.append(f"maxsulot_rasm/{filename}")
    await state.update_data(images=images)
    await msg.answer(f"✅ Rasm qo'shildi ({len(images)} ta).")

@dp.message(ProductState.images, F.text == "✅ Tugatish")
async def finish_product(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("images"):
        return await msg.answer("⚠️ Rasm yuboring!")
    category = await sync_to_async(Kategoriy.objects.get)(id=data['category_id'])
    product = await sync_to_async(UzumProduct.objects.create)(name=data['name'], price=data['price'], about=data['about'], category=category)
    for img_path in data.get("images", []):
        await sync_to_async(UzumProductImage.objects.create)(product=product, image=img_path)
    await msg.answer("✅ Mahsulot qo'shildi!", reply_markup=main_menu(msg.from_user.id))
    await state.clear()

@dp.message(F.text == "📩 Shikoyat yuborish")
async def support_start(msg: types.Message, state: FSMContext):
    await msg.answer("✍️ Shikoyatingizni yozing:", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Bekor qilish")]], resize_keyboard=True))
    await state.set_state(SupportState.message)

@dp.message(SupportState.message)
async def save_support(msg: types.Message, state: FSMContext):
    username = msg.from_user.username or f"user_{msg.from_user.id}"
    user, created = await sync_to_async(Users.objects.get_or_create)(username=username, defaults={"password": "!"})
    await sync_to_async(SupportMessage.objects.create)(user=user, message=msg.text)
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, f"📩 Yangi shikoyat\n👤 @{username}\n💬 {msg.text}")
        except: pass
    await msg.answer("✅ Shikoyatingiz yuborildi!", reply_markup=main_menu(msg.from_user.id))
    await state.clear()

@dp.message(F.text == "📋 Barcha shikoyatlar")
async def all_support(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS: return
    msgs = await sync_to_async(list)(SupportMessage.objects.select_related('user').order_by('-created_at')[:20])
    if not msgs: return await msg.answer("📭 Bo'sh")
    text = "📋 Oxirgi 20 ta shikoyat:\n\n"
    for m in msgs:
        text += f"👤 @{m.user.username}\n💬 {m.message}\n\n"
    await msg.answer(text)

# ╔══════════════════════════════════════════╗
# ║             USER PANEL KODI              ║
# ╚══════════════════════════════════════════╝

@dp.message(Command("login"))
async def cmd_login(msg: types.Message, state: FSMContext):
    user = await get_logged_user(msg.from_user.id)
    if user:
        await msg.answer(f"✅ Siz allaqachon *{user.username}* sifatida kirgansiz.", reply_markup=main_menu(msg.from_user.id), parse_mode="Markdown")
        return
    await msg.answer("👤 *Tizimga kirish*\n\nFoydalanuvchi nomingizni kiriting:", parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Bekor qilish")]], resize_keyboard=True))
    await state.set_state(LoginState.username)

@dp.message(LoginState.username)
async def login_get_username(msg: types.Message, state: FSMContext):
    username = msg.text.strip()
    exists = await sync_to_async(Users.objects.filter(username=username).exists)()
    if not exists:
        return await msg.answer("❌ Topilmadi. Qayta kiriting:")
    await state.update_data(username=username)
    await msg.answer("🔑 Parolingizni kiriting:")
    await state.set_state(LoginState.password)

@dp.message(LoginState.password)
async def login_get_password(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    from django.contrib.auth import authenticate as django_auth
    user = await sync_to_async(django_auth)(username=data['username'], password=msg.text)
    if user is None:
        return await msg.answer("❌ Parol noto'g'ri!")
    logged_in_users[msg.from_user.id] = user.id
    await state.clear()
    await msg.answer(f"✅ Xush kelibsiz, *{user.username}*!", reply_markup=main_menu(msg.from_user.id), parse_mode="Markdown")

@dp.message(F.text == "🚪 Chiqish")
async def logout(msg: types.Message):
    logged_in_users.pop(msg.from_user.id, None)
    await msg.answer("👋 Chiqdingiz.", reply_markup=main_menu(msg.from_user.id))

@dp.message(F.text == "❤️ Like'larim")
async def my_likes(msg: types.Message):
    if not await require_login(msg): return
    user = await get_logged_user(msg.from_user.id)
    likes = await sync_to_async(list)(Like.objects.filter(user=user).select_related('product'))
    if not likes: return await msg.answer("💔 Bo'sh")
    text = "❤️ Like'lar:\n"
    for l in likes: text += f"- {l.product.name}\n"
    await msg.answer(text)

@dp.message(F.text == "🛒 Savatim")
async def my_cart(msg: types.Message):
    if not await require_login(msg): return
    user = await get_logged_user(msg.from_user.id)
    items = await sync_to_async(list)(ShopingModel.objects.filter(user=user).select_related('product'))
    if not items: return await msg.answer("🛒 Savat bo'sh")
    text = "🛒 Savatingiz:\n"
    for i in items: text += f"- {i.product.name}\n"
    await msg.answer(text)

@dp.message(F.text == "📦 Buyurtmalarim")
async def my_orders(msg: types.Message):
    if not await require_login(msg): return
    user = await get_logged_user(msg.from_user.id)
    orders = await sync_to_async(list)(Order.objects.filter(user=user).order_by('-created_at')[:15])
    if not orders: return await msg.answer("📭 Buyurtma yo'q")
    buttons = [[InlineKeyboardButton(text=f"#{o.id} - {o.is_status}", callback_data=f"uorder_{o.id}")] for o in orders]
    await msg.answer("📦 Buyurtmalarim:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("uorder_"))
async def order_detail(call: types.CallbackQuery):
    user = await get_logged_user(call.from_user.id)
    oid = int(call.data.split("_")[1])
    order = await sync_to_async(Order.objects.get)(id=oid, user=user)
    items = await sync_to_async(list)(OrderItem.objects.filter(order=order).select_related('product'))
    text = f"📋 Buyurtma #{order.id}\nHolat: {order.is_status}\n\n"
    for i in items: text += f"- {i.product.name} x {i.count}\n"
    await call.message.answer(text)
    await call.answer()

@dp.message(F.text == "📊 Statistikam")
async def my_stats(msg: types.Message):
    if not await require_login(msg): return
    user = await get_logged_user(msg.from_user.id)
    ord_count = await sync_to_async(Order.objects.filter(user=user).count)()
    cart_count = await sync_to_async(ShopingModel.objects.filter(user=user).count)()
    await msg.answer(f"📊 {user.username}\nBuyurtmalar: {ord_count}\nSavatda: {cart_count}")

# ================= RUN =================
async def main():
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())