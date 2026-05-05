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

TOKEN = "8664343682:AAHIGZIxT25_cK44uu4-zamqzijradnhSC0"
ADMIN_IDS = [6411347321]

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)


# ─────────────────────────── STATES ───────────────────────────

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


# ─────────────────────────── SESSION ───────────────────────────

logged_in_users: dict[int, int] = {}


# ─────────────────────────── KEYBOARDS ───────────────────────────

def main_menu(user_id: int, is_logged: bool = False) -> ReplyKeyboardMarkup | ReplyKeyboardRemove:
    if user_id in ADMIN_IDS:
        kb = [
            [KeyboardButton(text="📦 Mahsulotlar")],
            [KeyboardButton(text="➕ Mahsulot qo'shish")],
            [KeyboardButton(text="📋 Barcha shikoyatlar"), KeyboardButton(text="📩 Shikoyat yuborish")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🚪 Chiqish")],
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    if is_logged:
        kb = [
            [KeyboardButton(text="📦 Mahsulotlar")],
            [KeyboardButton(text="📩 Shikoyat yuborish"), KeyboardButton(text="📜 Shikoyatlarim")],
            [KeyboardButton(text="❤️ Like'larim"), KeyboardButton(text="🛒 Savatim")],
            [KeyboardButton(text="📦 Buyurtmalarim")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🚪 Chiqish")],
        ]
        return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    return ReplyKeyboardRemove()


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Bekor qilish")]],
        resize_keyboard=True
    )


def done_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Tugatish"), KeyboardButton(text="🔙 Bekor qilish")]],
        resize_keyboard=True
    )


def product_detail_kb(pid: int, in_cart: bool = False) -> InlineKeyboardMarkup:
    cart_btn = (
        InlineKeyboardButton(text="🗑 Savatdan olib tashlash", callback_data=f"removecart_{pid}")
        if in_cart else
        InlineKeyboardButton(text="🛒 Savatga qo'shish", callback_data=f"addcart_{pid}")
    )
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❤️ Like", callback_data=f"like_{pid}")],
        [cart_btn],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_products")],
    ])


# ─────────────────────────── HELPERS ───────────────────────────

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
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔑 Tizimga kirish", callback_data="go_login")]
            ])
        )
        return False
    return True


async def send_product_card(target, product, tg_id: int, edit: bool = False):
    """Mahsulot kartasini yuborish yoki tahrirlash."""
    user = await get_logged_user(tg_id)

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

    in_cart = False
    if user:
        in_cart = await sync_to_async(
            ShopingModel.objects.filter(user=user, product=product).exists
        )()

    kb = product_detail_kb(product.id, in_cart)

    images = await sync_to_async(list)(UzumProductImage.objects.filter(product=product))
    if images:
        image_path = os.path.join(settings.MEDIA_ROOT, str(images[0].image))
        if os.path.exists(image_path):
            await target.answer_photo(
                photo=types.FSInputFile(image_path),
                caption=text, reply_markup=kb, parse_mode="Markdown"
            )
            return

    await target.answer(text, reply_markup=kb, parse_mode="Markdown")


# ─────────────────────────── /START ───────────────────────────

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


# ─────────────────────────── LOGIN ───────────────────────────

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


# ─────────────────────────── CANCEL ───────────────────────────

@dp.message(F.text == "🔙 Bekor qilish")
async def cancel_any(msg: types.Message, state: FSMContext):
    await state.clear()
    is_logged = msg.from_user.id in logged_in_users
    await msg.answer("❌ Amal bekor qilindi.", reply_markup=main_menu(msg.from_user.id, is_logged))


# ─────────────────────────── MAHSULOTLAR ───────────────────────────

@dp.message(F.text == "📦 Mahsulotlar")
async def products(msg: types.Message):
    if not await require_login(msg):
        return
    all_products = await sync_to_async(list)(UzumProduct.objects.filter(is_active=True))
    if not all_products:
        return await msg.answer("📭 Hozircha mahsulotlar mavjud emas.")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🛍 {p.name}  —  {p.price:,} so'm",
            callback_data=f"p_{p.id}"
        )]
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

    await send_product_card(call.message, product, call.from_user.id)
    await call.answer()


@dp.callback_query(F.data == "back_products")
async def back_products(call: types.CallbackQuery):
    all_products = await sync_to_async(list)(UzumProduct.objects.filter(is_active=True))
    if not all_products:
        await call.message.answer("📭 Hozircha mahsulotlar mavjud emas.")
        return await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🛍 {p.name}  —  {p.price:,} so'm",
            callback_data=f"p_{p.id}"
        )]
        for p in all_products
    ])
    await call.message.answer("📦 Mavjud mahsulotlar ro'yxati:", reply_markup=kb)
    await call.answer()


# ─────────────────────────── LIKE ───────────────────────────

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
        await call.answer("❤️ Mahsulot likelanganlarga qo'shildi!", show_alert=False)


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

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🛍 {l.product.name}", callback_data=f"p_{l.product.id}")]
        for l in likes
    ])
    await msg.answer(text, parse_mode="Markdown", reply_markup=kb)


# ─────────────────────────── SAVAT ───────────────────────────

@dp.callback_query(F.data.startswith("addcart_"))
async def add_to_cart(call: types.CallbackQuery):
    uid = call.from_user.id
    if uid not in logged_in_users:
        return await call.answer("🔐 Savatga qo'shish uchun tizimga kiring!", show_alert=True)
    user = await get_logged_user(uid)
    pid = int(call.data.split("_")[1])
    try:
        product = await sync_to_async(UzumProduct.objects.get)(id=pid)
    except UzumProduct.DoesNotExist:
        return await call.answer("⚠️ Mahsulot topilmadi!", show_alert=True)

    already = await sync_to_async(ShopingModel.objects.filter(user=user, product=product).exists)()
    if already:
        return await call.answer("⚠️ Bu mahsulot allaqachon savatingizda!", show_alert=True)

    await sync_to_async(ShopingModel.objects.create)(user=user, product=product)
    await call.answer("✅ Mahsulot savatga qo'shildi!", show_alert=False)

    # Tugmani yangilash
    kb = product_detail_kb(pid, in_cart=True)
    try:
        await call.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass


@dp.callback_query(F.data.startswith("removecart_"))
async def remove_from_cart(call: types.CallbackQuery):
    uid = call.from_user.id
    if uid not in logged_in_users:
        return await call.answer("🔐 Tizimga kiring!", show_alert=True)
    user = await get_logged_user(uid)
    pid = int(call.data.split("_")[1])
    try:
        product = await sync_to_async(UzumProduct.objects.get)(id=pid)
    except UzumProduct.DoesNotExist:
        return await call.answer("⚠️ Mahsulot topilmadi!", show_alert=True)

    await sync_to_async(ShopingModel.objects.filter(user=user, product=product).delete)()
    await call.answer("🗑 Mahsulot savatdan olib tashlandi.", show_alert=False)

    # Tugmani yangilash
    kb = product_detail_kb(pid, in_cart=False)
    try:
        await call.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass


@dp.message(F.text == "🛒 Savatim")
async def my_cart(msg: types.Message):
    if not await require_login(msg):
        return
    user = await get_logged_user(msg.from_user.id)
    items = await sync_to_async(list)(
        ShopingModel.objects.filter(user=user).select_related("product")
    )
    if not items:
        return await msg.answer("🛒 Savatingiz bo'sh.")

    text = "🛒 *Savatingiz:*\n\n"
    total = 0
    for i, item in enumerate(items, 1):
        text += f"{i}. {item.product.name} — {item.product.price:,} so'm\n"
        total += item.product.price
    text += f"\n💰 *Jami: {total:,} so'm*"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Buyurtma berish", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑 Savatni tozalash", callback_data="clear_cart")],
    ])
    await msg.answer(text, parse_mode="Markdown", reply_markup=kb)


@dp.callback_query(F.data == "clear_cart")
async def clear_cart(call: types.CallbackQuery):
    uid = call.from_user.id
    if uid not in logged_in_users:
        return await call.answer("🔐 Tizimga kiring!", show_alert=True)
    user = await get_logged_user(uid)
    await sync_to_async(ShopingModel.objects.filter(user=user).delete)()
    await call.answer("🗑 Savat tozalandi.", show_alert=False)
    try:
        await call.message.edit_text("🛒 Savatingiz bo'sh.", reply_markup=None)
    except Exception:
        await call.message.answer("🛒 Savatingiz bo'sh.")


@dp.callback_query(F.data == "checkout")
async def checkout(call: types.CallbackQuery):
    uid = call.from_user.id
    if uid not in logged_in_users:
        return await call.answer("🔐 Tizimga kiring!", show_alert=True)
    user = await get_logged_user(uid)

    items = await sync_to_async(list)(
        ShopingModel.objects.filter(user=user).select_related("product")
    )
    if not items:
        return await call.answer("🛒 Savatingiz bo'sh!", show_alert=True)

    # Order yaratish
    order = await sync_to_async(Order.objects.create)(user=user)
    total = 0
    order_text = f"📦 *Buyurtma #{order.id}*\n\n"
    for item in items:
        await sync_to_async(OrderItem.objects.create)(
            order=order,
            product=item.product,
            quantity=1,
            price=item.product.price
        )
        order_text += f"• {item.product.name} — {item.product.price:,} so'm\n"
        total += item.product.price

    order_text += f"\n💰 *Jami: {total:,} so'm*\n✅ Buyurtmangiz qabul qilindi!"

    # Savatni tozalash
    await sync_to_async(ShopingModel.objects.filter(user=user).delete)()

    await call.answer("✅ Buyurtma berildi!", show_alert=False)
    await call.message.answer(order_text, parse_mode="Markdown")

    # Adminga xabar
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🛒 *Yangi buyurtma #{order.id}!*\n\n"
                f"👤 Foydalanuvchi: @{user.username}\n"
                f"{order_text}",
                parse_mode="Markdown"
            )
        except Exception:
            pass


# ─────────────────────────── BUYURTMALAR ───────────────────────────

@dp.message(F.text == "📦 Buyurtmalarim")
async def my_orders(msg: types.Message):
    if not await require_login(msg):
        return
    user = await get_logged_user(msg.from_user.id)
    orders = await sync_to_async(list)(Order.objects.filter(user=user).order_by("-id")[:10])
    if not orders:
        return await msg.answer("📭 Siz hali buyurtma bermadingiz.")

    kb_rows = []
    for order in orders:
        date = order.created_at.strftime("%d.%m.%Y")
        kb_rows.append([
            InlineKeyboardButton(
                text=f"📦 #{order.id}  —  {date}",
                callback_data=f"order_{order.id}"
            )
        ])

    await msg.answer(
        "📦 *Buyurtmalaringiz:*\nBatafsil ko'rish uchun bosing 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows)
    )


@dp.callback_query(F.data.startswith("order_"))
async def order_detail(call: types.CallbackQuery):
    order_id = int(call.data.split("_")[1])
    uid = call.from_user.id

    if uid not in logged_in_users and uid not in ADMIN_IDS:
        return await call.answer("🔐 Tizimga kiring!", show_alert=True)

    try:
        order = await sync_to_async(Order.objects.get)(id=order_id)
    except Order.DoesNotExist:
        return await call.answer("⚠️ Buyurtma topilmadi!", show_alert=True)

    items = await sync_to_async(list)(
        OrderItem.objects.filter(order=order).select_related("product")
    )

    date = order.created_at.strftime("%d.%m.%Y %H:%M")
    text = f"📦 *Buyurtma #{order.id}*\n📅 Sana: {date}\n\n"
    total = 0
    for i, item in enumerate(items, 1):
        line_total = item.price * item.quantity
        text += f"{i}. {item.product.name} × {item.quantity} = {line_total:,} so'm\n"
        total += line_total
    text += f"\n💰 *Jami: {total:,} so'm*"

    await call.message.answer(text, parse_mode="Markdown")
    await call.answer()


# ─────────────────────────── STATISTIKA ───────────────────────────

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


# ─────────────────────────── SUPPORT ───────────────────────────

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


# ─────────────────────────── MAHSULOT QO'SHISH (ADMIN) ───────────────────────────

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
        await state.clear()
        return await msg.answer(
            "⚠️ Hech qanday kategoriya mavjud emas. Avval Django admin orqali kategoriya qo'shing.",
            reply_markup=main_menu(msg.from_user.id)
        )
    kb = [[KeyboardButton(text=c.name)] for c in cats]
    kb.append([KeyboardButton(text="🔙 Bekor qilish")])
    await msg.answer(
        "📂 Kategoriyani tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )
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


# ─────────────────────────── MAIN ───────────────────────────

async def main():
    logging.info("✅ Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())