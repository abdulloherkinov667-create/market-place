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

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings
from django.contrib.auth import authenticate as django_auth

from app.models import (
    UzumProduct, Kategoriy, SupportMessage,
    Users, UzumProductImage, Like,
    ShopingModel, Order, OrderItem
)

TOKEN = "8664343682:AAH4lSmtxkGCmZTUJhCrjk6T4anOrWUrj8c"
ADMIN_IDS = [6411347321]

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)


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


logged_in_users: dict[int, int] = {}


def main_menu(user_id, is_logged=False):
    if user_id in ADMIN_IDS:
        kb = [
            [KeyboardButton(text="📦 Mahsulotlar")],
            [KeyboardButton(text="➕ Mahsulot qo'shish")],
            [KeyboardButton(text="📋 Barcha shikoyatlar")],
            [KeyboardButton(text="📩 Shikoyat yuborish")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🚪 Chiqish")],
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    if is_logged:
        kb = [
            [KeyboardButton(text="📦 Mahsulotlar")],
            [KeyboardButton(text="📩 Shikoyat yuborish")],
            [KeyboardButton(text="📜 Shikoyatlarim")],
            [KeyboardButton(text="❤️ Like'larim"), KeyboardButton(text="🛒 Savatim")],
            [KeyboardButton(text="📦 Buyurtmalarim")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🚪 Chiqish")],
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    return ReplyKeyboardRemove()

def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Bekor qilish")]],
        resize_keyboard=True
    )

def done_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Tugatish"), KeyboardButton(text="🔙 Bekor qilish")]],
        resize_keyboard=True
    )


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
    if msg.from_user.id in ADMIN_IDS:
        return True
    user = await get_logged_user(msg.from_user.id)
    if not user:
        await msg.answer(
            "🔐 Bu bo'limga kirish uchun avval tizimga kirishingiz kerak.\n"
            "👇 /login buyrug'ini bosing.",
            reply_markup=ReplyKeyboardRemove()
        )
        return False
    return True


@dp.message(Command("start"))
async def start(msg: types.Message):
    uid = msg.from_user.id
    is_logged = uid in logged_in_users

    if uid in ADMIN_IDS:
        await msg.answer(
            "👑 Xush kelibsiz, Admin!\n\nQuyidagi menyu orqali boshqaruvni amalga oshiring.",
            reply_markup=main_menu(uid)
        )
    elif is_logged:
        user = await get_logged_user(uid)
        await msg.answer(
            f"👋 Xush kelibsiz, {user.username}!\n\nQuyidagi menyudan foydalaning.",
            reply_markup=main_menu(uid, is_logged=True)
        )
    else:
        await msg.answer(
            "👋 Assalomu alaykum! Botimizga xush kelibsiz!\n\n"
            "🔐 Botdan to'liq foydalanish uchun tizimga kirishingiz kerak.\n\n"
            "👇 Kirish uchun quyidagi tugmani bosing:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔑 Tizimga kirish", callback_data="go_login")]
            ])
        )

@dp.callback_query(F.data == "go_login")
async def go_login_cb(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("👤 Username kiriting:", reply_markup=cancel_kb())
    await state.set_state(LoginState.username)
    await call.answer()


@dp.message(Command("login"))
async def cmd_login(msg: types.Message, state: FSMContext):
    if msg.from_user.id in logged_in_users:
        user = await get_logged_user(msg.from_user.id)
        return await msg.answer(
            f"✅ Siz allaqachon tizimdasiz: {user.username}",
            reply_markup=main_menu(msg.from_user.id, True)
        )
    await msg.answer("👤 Username kiriting:", reply_markup=cancel_kb())
    await state.set_state(LoginState.username)

@dp.message(LoginState.username)
async def login_username(msg: types.Message, state: FSMContext):
    if msg.text == "🔙 Bekor qilish":
        await state.clear()
        return await msg.answer("❌ Bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    username = msg.text.strip()
    exists = await sync_to_async(Users.objects.filter(username=username).exists)()
    if not exists:
        return await msg.answer("❌ Bunday foydalanuvchi topilmadi.\nUsername'ni to'g'ri kiriting:")
    await state.update_data(username=username)
    await msg.answer("🔑 Parolni kiriting:")
    await state.set_state(LoginState.password)

@dp.message(LoginState.password)
async def login_password(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    user = await sync_to_async(django_auth)(username=data["username"], password=msg.text)
    if user is None:
        return await msg.answer("❌ Parol noto'g'ri! Qaytadan urinib ko'ring:")
    logged_in_users[msg.from_user.id] = user.id
    await state.clear()
    await msg.answer(
        f"✅ Muvaffaqiyatli kirdingiz!\n👋 Xush kelibsiz, {user.username}!",
        reply_markup=main_menu(msg.from_user.id, is_logged=True)
    )

@dp.message(F.text == "🚪 Chiqish")
async def logout(msg: types.Message):
    logged_in_users.pop(msg.from_user.id, None)
    await msg.answer(
        "👋 Tizimdan muvaffaqiyatli chiqdingiz.\nQayta kirish uchun /login bosing.",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(F.text == "🔙 Bekor qilish")
async def cancel_any(msg: types.Message, state: FSMContext):
    await state.clear()
    is_logged = msg.from_user.id in logged_in_users
    await msg.answer("❌ Amal bekor qilindi.", reply_markup=main_menu(msg.from_user.id, is_logged))


@dp.message(F.text == "📦 Mahsulotlar")
async def products(msg: types.Message):
    if not await require_login(msg):
        return
    all_products = await sync_to_async(list)(UzumProduct.objects.filter(is_active=True))
    if not all_products:
        return await msg.answer("📭 Hozircha mahsulotlar mavjud emas.")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🛍 {p.name}  —  {p.price:,} so'm", callback_data=f"p_{p.id}")]
        for p in all_products
    ])
    await msg.answer("📦 Mavjud mahsulotlar ro'yxati:", reply_markup=kb)

@dp.callback_query(F.data.startswith("p_"))
async def product_detail(call: types.CallbackQuery):
    pid = int(call.data.split("_")[1])
    try:
        product = await sync_to_async(UzumProduct.objects.get)(id=pid)
    except UzumProduct.DoesNotExist:
        return await call.answer("⚠️ Mahsulot topilmadi!", show_alert=True)

    discount_text = ""
    if product.aksi_narx and product.aksi_narx > 0:
        discounted = int(product.price * (1 - product.aksi_narx / 100))
        discount_text = f"\n🔖 Aksiya: -{product.aksi_narx}%  →  {discounted:,} so'm"

    text = (
        f"🛍 *{product.name}*\n"
        f"💰 Narxi: {product.price:,} so'm"
        f"{discount_text}\n\n"
        f"📄 {product.about}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❤️ Like", callback_data=f"like_{pid}")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_products")],
    ])

    images = await sync_to_async(list)(UzumProductImage.objects.filter(product=product))
    if images:
        image_path = os.path.join(settings.MEDIA_ROOT, str(images[0].image))
        if os.path.exists(image_path):
            await call.message.answer_photo(
                photo=types.FSInputFile(image_path),
                caption=text, reply_markup=kb, parse_mode="Markdown"
            )
        else:
            await call.message.answer(text + "\n\n⚠️ Rasm yuklanmagan.", reply_markup=kb, parse_mode="Markdown")
    else:
        await call.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "back_products")
async def back_products(call: types.CallbackQuery):
    all_products = await sync_to_async(list)(UzumProduct.objects.filter(is_active=True))
    if not all_products:
        await call.message.answer("📭 Hozircha mahsulotlar mavjud emas.")
        return await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🛍 {p.name}  —  {p.price:,} so'm", callback_data=f"p_{p.id}")]
        for p in all_products
    ])
    await call.message.answer("📦 Mavjud mahsulotlar ro'yxati:", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("like_"))
async def toggle_like(call: types.CallbackQuery):
    uid = call.from_user.id
    if uid not in logged_in_users:
        return await call.answer("🔐 Like bosish uchun tizimga kiring!", show_alert=True)
    user = await get_logged_user(uid)
    pid = int(call.data.split("_")[1])
    try:
        product = await sync_to_async(UzumProduct.objects.get)(id=pid)
    except UzumProduct.DoesNotExist:
        return await call.answer("⚠️ Mahsulot topilmadi!", show_alert=True)

    like_exists = await sync_to_async(Like.objects.filter(user=user, product=product).exists)()
    if like_exists:
        await sync_to_async(Like.objects.filter(user=user, product=product).delete)()
        await call.answer("💔 Like olib tashlandi.", show_alert=False)
    else:
        await sync_to_async(Like.objects.create)(user=user, product=product)
        await call.answer("❤️ Mahsulot like'langanlarga qo'shildi!", show_alert=False)


@dp.message(F.text == "❤️ Like'larim")
async def my_likes(msg: types.Message):
    if not await require_login(msg):
        return
    user = await get_logged_user(msg.from_user.id)
    likes = await sync_to_async(list)(Like.objects.filter(user=user).select_related("product"))
    if not likes:
        return await msg.answer("💔 Siz hali hech qanday mahsulotni like qilmagansiz.")
    text = "❤️ *Like'langan mahsulotlar:*\n\n"
    for i, l in enumerate(likes, 1):
        text += f"{i}. {l.product.name} — {l.product.price:,} so'm\n"
    await msg.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🛒 Savatim")
async def my_cart(msg: types.Message):
    if not await require_login(msg):
        return
    user = await get_logged_user(msg.from_user.id)
    items = await sync_to_async(list)(ShopingModel.objects.filter(user=user).select_related("product"))
    if not items:
        return await msg.answer("🛒 Savatingiz bo'sh.")
    text = "🛒 *Savatingiz:*\n\n"
    total = 0
    for i, item in enumerate(items, 1):
        text += f"{i}. {item.product.name} — {item.product.price:,} so'm\n"
        total += item.product.price
    text += f"\n💰 *Jami: {total:,} so'm*"
    await msg.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📦 Buyurtmalarim")
async def my_orders(msg: types.Message):
    if not await require_login(msg):
        return
    user = await get_logged_user(msg.from_user.id)
    orders = await sync_to_async(list)(Order.objects.filter(user=user).order_by("-id")[:10])
    if not orders:
        return await msg.answer("📭 Siz hali buyurtma bermadingiz.")
    text = "📦 *Buyurtmalaringiz:*\n\n"
    for i, order in enumerate(orders, 1):
        date = order.created_at.strftime("%d.%m.%Y")
        text += f"{i}. Buyurtma #{order.id} — {date}\n"
    await msg.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📊 Statistika")
async def my_stats(msg: types.Message):
    if not await require_login(msg):
        return
    uid = msg.from_user.id

    if uid in ADMIN_IDS:
        total_users = await sync_to_async(Users.objects.count)()
        total_products = await sync_to_async(UzumProduct.objects.filter(is_active=True).count)()
        total_orders = await sync_to_async(Order.objects.count)()
        total_support = await sync_to_async(SupportMessage.objects.count)()
        text = (
            "📊 *Admin statistikasi:*\n\n"
            f"👥 Foydalanuvchilar: {total_users}\n"
            f"📦 Aktiv mahsulotlar: {total_products}\n"
            f"🛒 Jami buyurtmalar: {total_orders}\n"
            f"📩 Jami shikoyatlar: {total_support}"
        )
    else:
        user = await get_logged_user(uid)
        ord_count = await sync_to_async(Order.objects.filter(user=user).count)()
        cart_count = await sync_to_async(ShopingModel.objects.filter(user=user).count)()
        like_count = await sync_to_async(Like.objects.filter(user=user).count)()
        text = (
            f"📊 *{user.username} statistikasi:*\n\n"
            f"🛒 Savatdagi mahsulotlar: {cart_count}\n"
            f"📦 Buyurtmalar soni: {ord_count}\n"
            f"❤️ Like'lar soni: {like_count}"
        )
    await msg.answer(text, parse_mode="Markdown")


@dp.message(F.text == "📩 Shikoyat yuborish")
async def support_start(msg: types.Message, state: FSMContext):
    if not await require_login(msg):
        return
    await msg.answer(
        "📩 Shikoyat yoki taklifingizni yozing.\n"
        "Biz sizning xabaringizni ko'rib chiqamiz va tez orada javob beramiz:",
        reply_markup=cancel_kb()
    )
    await state.set_state(SupportState.message)

@dp.message(SupportState.message)
async def support_receive(msg: types.Message, state: FSMContext):
    if msg.text == "🔙 Bekor qilish":
        await state.clear()
        is_logged = msg.from_user.id in logged_in_users
        return await msg.answer("❌ Bekor qilindi.", reply_markup=main_menu(msg.from_user.id, is_logged))

    uid = msg.from_user.id
    user = None if uid in ADMIN_IDS else await get_logged_user(uid)

    if user is None and uid not in ADMIN_IDS:
        await state.clear()
        return await msg.answer("🔐 Tizimga kiring.", reply_markup=ReplyKeyboardRemove())

    await sync_to_async(SupportMessage.objects.create)(user=user, message=msg.text)
    await state.clear()
    is_logged = uid in logged_in_users
    await msg.answer(
        "✅ Shikoyatingiz muvaffaqiyatli yuborildi!\n"
        "📋 Tez orada ko'rib chiqamiz. Rahmat!",
        reply_markup=main_menu(uid, is_logged)
    )

    for admin_id in ADMIN_IDS:
        try:
            username_text = f"@{user.username}" if user else "Admin"
            await bot.send_message(
                admin_id,
                f"📩 *Yangi shikoyat!*\n\n"
                f"👤 Foydalanuvchi: {username_text}\n"
                f"💬 Xabar: {msg.text}",
                parse_mode="Markdown"
            )
        except Exception:
            pass

@dp.message(F.text == "📜 Shikoyatlarim")
async def my_support(msg: types.Message):
    if not await require_login(msg):
        return
    user = await get_logged_user(msg.from_user.id)
    if not user:
        return
    msgs = await sync_to_async(list)(
        SupportMessage.objects.filter(user=user).order_by("-created_at")[:10]
    )
    if not msgs:
        return await msg.answer("📭 Siz hali shikoyat yubormadingiz.")
    text = "📜 *Shikoyatlaringiz tarixi:*\n\n"
    for i, m in enumerate(msgs, 1):
        date = m.created_at.strftime("%d.%m.%Y %H:%M")
        text += f"{i}. [{date}]\n💬 {m.message}\n\n"
    await msg.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📋 Barcha shikoyatlar")
async def all_support(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    msgs = await sync_to_async(list)(
        SupportMessage.objects.select_related("user").order_by("-created_at")[:20]
    )
    if not msgs:
        return await msg.answer("📭 Hozircha shikoyatlar yo'q.")
    text = "📋 *Oxirgi 20 ta shikoyat:*\n\n"
    for i, m in enumerate(msgs, 1):
        date = m.created_at.strftime("%d.%m.%Y %H:%M")
        username = f"@{m.user.username}" if m.user else "Noma'lum"
        text += f"{i}. {username} [{date}]\n💬 {m.message}\n\n"
    await msg.answer(text, parse_mode="Markdown")


@dp.message(F.text == "➕ Mahsulot qo'shish")
async def add_product(msg: types.Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS:
        return
    await msg.answer("📝 Mahsulot nomini kiriting:", reply_markup=cancel_kb())
    await state.set_state(ProductState.name)

@dp.message(ProductState.name)
async def get_name(msg: types.Message, state: FSMContext):
    if msg.text == "🔙 Bekor qilish":
        await state.clear()
        return await msg.answer("❌ Bekor qilindi.", reply_markup=main_menu(msg.from_user.id))
    await state.update_data(name=msg.text)
    cats = await sync_to_async(list)(Kategoriy.objects.all())
    if not cats:
        await msg.answer("⚠️ Hech qanday kategoriya mavjud emas. Avval kategoriya qo'shing.")
        await state.clear()
        return
    kb = [[KeyboardButton(text=c.name)] for c in cats]
    kb.append([KeyboardButton(text="🔙 Bekor qilish")])
    await msg.answer("📂 Kategoriyani tanlang:", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))
    await state.set_state(ProductState.category)

@dp.message(ProductState.category)
async def get_category(msg: types.Message, state: FSMContext):
    if msg.text == "🔙 Bekor qilish":
        await state.clear()
        return await msg.answer("❌ Bekor qilindi.", reply_markup=main_menu(msg.from_user.id))
    try:
        category = await sync_to_async(Kategoriy.objects.get)(name=msg.text)
        await state.update_data(category_id=category.id)
        await msg.answer("💰 Mahsulot narxini kiriting (so'mda):", reply_markup=cancel_kb())
        await state.set_state(ProductState.price)
    except Kategoriy.DoesNotExist:
        await msg.answer("❌ Iltimos, ro'yxatdan kategoriya tanlang.")

@dp.message(ProductState.price)
async def get_price(msg: types.Message, state: FSMContext):
    if msg.text == "🔙 Bekor qilish":
        await state.clear()
        return await msg.answer("❌ Bekor qilindi.", reply_markup=main_menu(msg.from_user.id))
    if not msg.text.isdigit():
        return await msg.answer("❌ Faqat raqam kiriting! Masalan: 50000")
    await state.update_data(price=int(msg.text))
    await msg.answer("📄 Mahsulot haqida ma'lumot yozing:", reply_markup=cancel_kb())
    await state.set_state(ProductState.about)

@dp.message(ProductState.about)
async def get_about(msg: types.Message, state: FSMContext):
    if msg.text == "🔙 Bekor qilish":
        await state.clear()
        return await msg.answer("❌ Bekor qilindi.", reply_markup=main_menu(msg.from_user.id))
    await state.update_data(about=msg.text, images=[])
    await msg.answer(
        "🖼 Mahsulot rasmlarini yuboring.\n"
        "Barcha rasmlarni yuborganingizdan so'ng ✅ Tugatish tugmasini bosing:",
        reply_markup=done_kb()
    )
    await state.set_state(ProductState.images)

@dp.message(ProductState.images, F.photo)
async def get_images(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    images = data.get("images", [])
    file = await bot.get_file(msg.photo[-1].file_id)
    downloaded = await bot.download_file(file.file_path)
    save_dir = os.path.join(settings.MEDIA_ROOT, "maxsulot_rasm")
    os.makedirs(save_dir, exist_ok=True)
    filename = f"{msg.photo[-1].file_id}.jpg"
    full_path = os.path.join(save_dir, filename)
    with open(full_path, "wb") as f:
        f.write(downloaded.read())
    images.append(f"maxsulot_rasm/{filename}")
    await state.update_data(images=images)
    await msg.answer(
        f"✅ Rasm qabul qilindi! (Jami: {len(images)} ta)\n"
        "Yana rasm yuboring yoki ✅ Tugatish tugmasini bosing."
    )

@dp.message(ProductState.images, F.text == "✅ Tugatish")
async def finish_product(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("images"):
        return await msg.answer("⚠️ Kamida bitta rasm yuborishingiz kerak!")
    category = await sync_to_async(Kategoriy.objects.get)(id=data["category_id"])
    product = await sync_to_async(UzumProduct.objects.create)(
        name=data["name"],
        price=data["price"],
        about=data["about"],
        category=category
    )
    for img_path in data["images"]:
        await sync_to_async(UzumProductImage.objects.create)(product=product, image=img_path)
    await state.clear()
    await msg.answer(
        f"✅ Mahsulot muvaffaqiyatli qo'shildi!\n\n"
        f"📦 Nomi: {product.name}\n"
        f"💰 Narxi: {product.price:,} so'm\n"
        f"🖼 Rasmlar: {len(data['images'])} ta",
        reply_markup=main_menu(msg.from_user.id)
    )

@dp.message(ProductState.images)
async def images_invalid(msg: types.Message):
    await msg.answer("📸 Iltimos, faqat rasm yuboring yoki ✅ Tugatish tugmasini bosing.")


async def main():
    logging.info("✅ Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())