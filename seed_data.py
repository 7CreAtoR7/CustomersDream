"""Seed test data: many categories with subcategories and mockups.

Each mockup carries:
  - price_cents  -> price in cents (USD)
  - platform     -> site | bot | app
  - complexity   -> simple | medium | complex
These power the catalog filter chips.
"""
import asyncio
import sys

sys.path.insert(0, ".")

from bot.database.db import async_session_factory, engine
from bot.database.models import Base, Category, Mockup, Subcategory


IMG_BASE = "/assets/mockups/products"


def m(title, desc, price, platform, complexity, features, image):
    return {
        "title": title,
        "description": desc,
        "price_cents": price * 100,
        "platform": platform,
        "complexity": complexity,
        "features": features,
        "image_url": f"{IMG_BASE}/{image}.png",
    }


# Structure rule: one category -> several subproducts (subcategories),
# and EXACTLY ONE product (mockup) per subproduct. Every product has its
# own distinct preview image (image_url).
SEED = [
    {
        "name": "Крипта и финансы", "emoji": "₿", "position": 1,
        "subcategories": [
            {"name": "Криптобиржи", "mockups": [
                m("CryptoExchange Pro", "Полнофункциональная криптобиржа с P2P-торговлей, стаканом ордеров и графиками TradingView.", 2500, "site", "complex",
                  "P2P торговля\nСтакан ордеров\nTradingView графики\nKYC верификация\nМультивалютный кошелёк\nAPI для ботов", "crypto-exchange-pro"),
            ]},
            {"name": "DeFi-сервисы", "mockups": [
                m("DeFi Dashboard", "Панель управления DeFi-портфелем: стейкинг, фарминг, свопы через DEX-агрегатор.", 1800, "app", "complex",
                  "DeFi агрегатор\nСтейкинг пулы\nYield фарминг\nСвопы\nПортфель-трекер\nМультичейн", "defi-dashboard"),
            ]},
            {"name": "Криптокошельки", "mockups": [
                m("MultiWallet", "Мультивалютный кошелёк с поддержкой 50+ сетей, свопами и NFT-галереей.", 1500, "app", "medium",
                  "50+ блокчейнов\nВстроенные свопы\nNFT галерея\nStaking\nБиометрия\nSeed-фраза бэкап", "multiwallet"),
            ]},
            {"name": "Обменники", "mockups": [
                m("FastSwap", "Мгновенный обменник крипты с фиксированным курсом и реферальной программой.", 900, "site", "simple",
                  "Обмен крипты\nФиксированный курс\nРеферальная программа\nИстория сделок\nПоддержка фиата", "fastswap"),
            ]},
        ],
    },
    {
        "name": "Казино и гемблинг", "emoji": "🎰", "position": 2,
        "subcategories": [
            {"name": "Онлайн-казино", "mockups": [
                m("LuxBet Casino", "Премиальное онлайн-казино: слоты, рулетка, live-дилеры, крипто-депозиты.", 3500, "site", "complex",
                  "1000+ слотов\nLive-дилеры\nКрипто-депозиты\nVIP программа\nТурниры\nАдмин-панель", "luxbet-casino"),
            ]},
            {"name": "Краш-игры", "mockups": [
                m("Crash Game Platform", "Платформа с краш-играми, dice, mines. Provably fair, моментальные выплаты.", 1200, "site", "medium",
                  "Crash game\nDice\nMines\nProvably Fair\nМоментальные выплаты\nРеферальная система", "crash-game"),
            ]},
            {"name": "Букмекеры", "mockups": [
                m("BetFast Sportsbook", "Букмекерская контора с live-ставками, статистикой матчей и мультиставками.", 4000, "site", "complex",
                  "Live-ставки\nПре-матч линия\nСтатистика\nМультиставки\nCash-out\nМобильное приложение", "betfast-sportsbook"),
            ]},
            {"name": "Telegram-казино боты", "mockups": [
                m("TG Slots Bot", "Telegram-бот казино со слотами, рулеткой и системой крипто-депозитов.", 800, "bot", "medium",
                  "Слоты в Telegram\nРулетка\nКрипто-депозиты\nАвтовыплаты\nРеферальная система\nАдмин-панель", "tg-slots-bot"),
            ]},
        ],
    },
    {
        "name": "Маркетплейсы", "emoji": "🛒", "position": 3,
        "subcategories": [
            {"name": "Универсальные", "mockups": [
                m("MegaMarket", "Маркетплейс с витриной товаров, корзиной, оплатой и кабинетом продавца.", 2800, "site", "complex",
                  "Витрина товаров\nКорзина и оплата\nКабинет продавца\nОтзывы и рейтинги\nДоставка\nАдмин-панель", "megamarket"),
            ]},
            {"name": "Хендмейд", "mockups": [
                m("HandMade Market", "Маркетплейс для мастеров ручной работы с галереей и заказами.", 1500, "site", "medium",
                  "Галерея работ\nЗаказы\nЧат с мастером\nОплата\nПрофили мастеров", "handmade-market"),
            ]},
            {"name": "Цифровые товары", "mockups": [
                m("Digital Goods Bot", "Telegram-бот для продажи цифровых товаров с автовыдачей.", 600, "bot", "simple",
                  "Каталог товаров\nАвтовыдача\nОплата криптой\nСтатистика продаж", "digital-goods-bot"),
            ]},
        ],
    },
    {
        "name": "Рестораны и кафе", "emoji": "🍽", "position": 4,
        "subcategories": [
            {"name": "Доставка еды", "mockups": [
                m("FoodExpress", "Сайт доставки еды с меню, корзиной, онлайн-оплатой и трекингом заказа.", 1600, "site", "medium",
                  "Меню с фото\nКорзина\nОнлайн-оплата\nТрекинг заказа\nПромокоды\nАдмин-панель", "foodexpress"),
            ]},
            {"name": "Бот заказов", "mockups": [
                m("Resto Bot", "Telegram-бот для приёма заказов из ресторана с оплатой.", 500, "bot", "simple",
                  "Меню\nЗаказ в боте\nОплата\nУведомления\nКорзина", "resto-bot"),
            ]},
            {"name": "Бронирование столов", "mockups": [
                m("TableBook", "Сайт бронирования столиков с выбором времени и зала.", 1100, "site", "medium",
                  "Выбор стола\nКалендарь\nПодтверждение\nНапоминания\nОтзывы", "tablebook"),
            ]},
        ],
    },
    {
        "name": "Онлайн-образование", "emoji": "🎓", "position": 5,
        "subcategories": [
            {"name": "Курсы и LMS", "mockups": [
                m("EduPlatform", "Платформа онлайн-курсов с видео-уроками, тестами и сертификатами.", 2200, "site", "complex",
                  "Видео-уроки\nТесты\nСертификаты\nПрогресс\nОплата курсов\nЛичный кабинет", "eduplatform"),
            ]},
            {"name": "Репетиторы", "mockups": [
                m("TutorMatch", "Сайт подбора репетиторов с расписанием и оплатой занятий.", 1300, "site", "medium",
                  "Поиск репетитора\nРасписание\nОплата\nВидеосвязь\nОтзывы", "tutormatch"),
            ]},
        ],
    },
    {
        "name": "Бьюти и спа", "emoji": "💅", "position": 6,
        "subcategories": [
            {"name": "Салоны красоты", "mockups": [
                m("BeautySalon", "Сайт салона красоты с услугами, онлайн-записью и портфолио мастеров.", 1200, "site", "simple",
                  "Услуги и цены\nОнлайн-запись\nПортфолио\nМастера\nАкции", "beautysalon"),
            ]},
            {"name": "Бот записи", "mockups": [
                m("Booking Bot", "Telegram-бот записи в салон с напоминаниями.", 450, "bot", "simple",
                  "Онлайн-запись\nНапоминания\nВыбор мастера\nОтмена записи", "booking-bot"),
            ]},
        ],
    },
    {
        "name": "Фитнес и спорт", "emoji": "🏋", "position": 7,
        "subcategories": [
            {"name": "Фитнес-клубы", "mockups": [
                m("FitClub", "Сайт фитнес-клуба с абонементами, расписанием и тренерами.", 1400, "site", "medium",
                  "Абонементы\nРасписание\nТренеры\nОнлайн-оплата\nЛичный кабинет", "fitclub"),
            ]},
            {"name": "Приложения тренировок", "mockups": [
                m("WorkoutApp", "Мобильное приложение с программами тренировок и трекингом прогресса.", 2000, "app", "complex",
                  "Программы тренировок\nТрекинг прогресса\nВидео-упражнения\nПодписка\nСтатистика", "workout-app"),
            ]},
        ],
    },
    {
        "name": "Медицина и клиники", "emoji": "🩺", "position": 8,
        "subcategories": [
            {"name": "Клиники", "mockups": [
                m("MediClinic", "Сайт клиники с услугами, врачами и онлайн-записью на приём.", 1700, "site", "medium",
                  "Услуги\nВрачи\nОнлайн-запись\nЛичный кабинет\nАнализы онлайн", "mediclinic"),
            ]},
            {"name": "Телемедицина", "mockups": [
                m("TeleHealth", "Платформа телемедицины с видео-консультациями и рецептами.", 2600, "app", "complex",
                  "Видео-консультации\nЭлектронные рецепты\nИстория болезни\nОплата\nЧат с врачом", "telehealth"),
            ]},
        ],
    },
    {
        "name": "Тревел и туризм", "emoji": "✈", "position": 9,
        "subcategories": [
            {"name": "Бронирование туров", "mockups": [
                m("TravelGo", "Сайт турагентства с поиском туров, бронированием и оплатой.", 1900, "site", "complex",
                  "Поиск туров\nБронирование\nОплата\nОтзывы\nЛичный кабинет\nГорящие туры", "travelgo"),
            ]},
            {"name": "Аренда жилья", "mockups": [
                m("StayRent", "Сайт аренды жилья с картой, фильтрами и онлайн-бронированием.", 2100, "site", "complex",
                  "Карта объектов\nФильтры\nБронирование\nОплата\nОтзывы\nКалендарь", "stayrent"),
            ]},
        ],
    },
    {
        "name": "Авто", "emoji": "🚗", "position": 10,
        "subcategories": [
            {"name": "Автосалоны", "mockups": [
                m("AutoShowroom", "Сайт автосалона с каталогом авто, фильтрами и заявкой на тест-драйв.", 1500, "site", "medium",
                  "Каталог авто\nФильтры\nТест-драйв\nКредит-калькулятор\nЗаявки", "autoshowroom"),
            ]},
            {"name": "Автосервисы", "mockups": [
                m("AutoService", "Сайт автосервиса с услугами, ценами и онлайн-записью.", 1000, "site", "simple",
                  "Услуги\nЦены\nОнлайн-запись\nОтзывы\nКонтакты", "autoservice"),
            ]},
        ],
    },
    {
        "name": "Недвижимость", "emoji": "🏠", "position": 11,
        "subcategories": [
            {"name": "Агентства", "mockups": [
                m("RealEstate Pro", "Сайт агентства недвижимости с каталогом объектов, картой и фильтрами.", 2400, "site", "complex",
                  "Каталог объектов\nКарта\nФильтры\nИпотека-калькулятор\nЗаявки\nЛичный кабинет", "realestate-pro"),
            ]},
            {"name": "Новостройки", "mockups": [
                m("NewBuild", "Лендинг жилого комплекса с планировками, ценами и формой заявки.", 1100, "site", "simple",
                  "Планировки\nЦены\nГалерея\nФорма заявки\nИнтерактивная карта", "newbuild"),
            ]},
        ],
    },
    {
        "name": "Услуги и сервисы", "emoji": "🛠", "position": 12,
        "subcategories": [
            {"name": "Лендинги", "mockups": [
                m("Service Landing", "Универсальный продающий лендинг для услуг с формой заявки.", 700, "site", "simple",
                  "Продающий блок\nУслуги\nОтзывы\nФорма заявки\nИнтеграция с CRM", "service-landing"),
            ]},
            {"name": "CRM-системы", "mockups": [
                m("BizCRM", "CRM-система для бизнеса с воронкой продаж и аналитикой.", 3000, "app", "complex",
                  "Воронка продаж\nКлиентская база\nАналитика\nЗадачи\nИнтеграции\nОтчёты", "bizcrm"),
            ]},
            {"name": "Лид-боты", "mockups": [
                m("Lead Bot", "Telegram-бот для сбора и обработки заявок с уведомлениями.", 550, "bot", "simple",
                  "Сбор заявок\nУведомления\nCRM-интеграция\nСтатистика", "lead-bot"),
            ]},
        ],
    },
]


async def seed():
    # Rebuild schema so new columns (platform, complexity) are applied.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        for cat_data in SEED:
            cat = Category(
                name=cat_data["name"],
                emoji=cat_data["emoji"],
                position=cat_data["position"],
            )
            session.add(cat)
            await session.flush()

            for i, sub_data in enumerate(cat_data["subcategories"]):
                sub = Subcategory(category_id=cat.id, name=sub_data["name"], position=i)
                session.add(sub)
                await session.flush()

                for j, mk in enumerate(sub_data["mockups"]):
                    session.add(Mockup(
                        subcategory_id=sub.id,
                        title=mk["title"],
                        description=mk["description"],
                        price_cents=mk["price_cents"],
                        currency="USD",
                        features=mk["features"],
                        platform=mk["platform"],
                        complexity=mk["complexity"],
                        image_url=mk["image_url"],
                        position=j,
                    ))

        await session.commit()
    await engine.dispose()
    total_cats = len(SEED)
    total_mockups = sum(len(s["mockups"]) for c in SEED for s in c["subcategories"])
    print(f"Seed OK: {total_cats} categories, {total_mockups} mockups inserted.")


if __name__ == "__main__":
    asyncio.run(seed())
