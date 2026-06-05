# Деплой CustomersDream на timeweb.cloud (24/7)

Бот + Mini App будут крутиться на VPS под управлением `systemd`, а nginx
будет отдавать наружу HTTPS (Telegram Mini App работает только по https).

Схема: **Telegram → nginx (443, SSL) → uvicorn (127.0.0.1:8888) → FastAPI + бот**

---

## 0. Что понадобится

- Аккаунт на [timeweb.cloud](https://timeweb.cloud)
- **Домен** (Telegram требует HTTPS, а сертификат Let's Encrypt выдаётся на домен).
  Можно купить дешёвый домен (.ru / .site) или привязать любой свой.
- Токен бота (он уже в `.env`).

---

## 1. Создать облачный сервер (VPS)

1. В панели timeweb.cloud: **Облачные серверы → Создать**.
2. ОС: **Ubuntu 24.04**.
3. Тариф: самый младший хватит (1 CPU / 1–2 GB RAM).
4. Регион: ближайший (например, Москва/СПб).
5. Создай и сохрани **root-пароль** (или загрузи SSH-ключ).
6. После создания запиши **IP-адрес** сервера (например, `185.12.34.56`).

---

## 2. Привязать домен к серверу

В настройках DNS своего домена создай A-запись:

```
@    A    185.12.34.56     (IP твоего сервера)
```

Подожди 5–30 минут, пока DNS обновится. Проверить можно: `ping your-domain.ru`
должен показать твой IP.

---

## 3. Подключиться к серверу

С Windows (PowerShell):

```powershell
ssh root@185.12.34.56
```

Введи пароль из панели.

---

## 4. Установить зависимости системы

```bash
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip git nginx
```

---

## 5. Залить код на сервер

**Вариант A — через Git** (если проект на GitHub):

```bash
cd /opt
git clone https://github.com/ТВОЙ_АККАУНТ/CustomersDream.git
cd CustomersDream
```

**Вариант B — без Git, скопировать с компьютера.**
На своём ПК (PowerShell), из папки проекта:

```powershell
scp -r . root@185.12.34.56:/opt/CustomersDream
```

> `.env` и папка `data/` в `.gitignore` — при варианте A их нужно создать на
> сервере вручную (см. шаг 6). При варианте B `.env` скопируется вместе с кодом.

---

## 6. Создать виртуальное окружение и .env

```bash
cd /opt/CustomersDream
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Создать/проверить `.env` (если заливал через Git — создай заново):

```bash
nano .env
```

Содержимое (главное — `WEBAPP_URL` теперь это твой домен с https):

```env
BOT_TOKEN=8822915447:AAEXaTWv-CLsqzCcq707vMnBv606wPSzgnE
ADMIN_IDS=827190946,6078078151
MANAGER_USERNAME=il1aLis
CRYPTO_USDT_TRC20=
DEFAULT_CURRENCY=USD
DATABASE_URL=sqlite+aiosqlite:///./data/bot.db
WEBAPP_URL=https://your-domain.ru
```

Сохранить: `Ctrl+O`, `Enter`, `Ctrl+X`.

Заполнить базу тестовыми данными (один раз):

```bash
python seed_data.py
```

---

## 7. Настроить nginx + HTTPS

Скопировать конфиг и заменить домен:

```bash
cp /opt/CustomersDream/deploy/nginx.conf /etc/nginx/sites-available/customersdream
# заменить your-domain.ru на свой домен:
sed -i 's/your-domain.ru/ВАШ-домен.ru/g' /etc/nginx/sites-available/customersdream

ln -s /etc/nginx/sites-available/customersdream /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

Выпустить SSL-сертификат (бесплатный, Let's Encrypt):

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d ВАШ-домен.ru
```

Certbot спросит email, согласие и предложит редирект http→https — выбирай **да (2)**.
Сертификат продлевается автоматически.

---

## 8. Запустить бота как сервис (24/7, автозапуск)

```bash
cp /opt/CustomersDream/deploy/customersdream.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable customersdream
systemctl start customersdream
```

Проверить статус и логи:

```bash
systemctl status customersdream
journalctl -u customersdream -f
```

Должно быть `active (running)` и в логах `Bot is starting`.

---

## 9. Прописать домен в BotFather (важно!)

Чтобы кнопка Mini App открывалась:

1. В Telegram → @BotFather → `/mybots` → выбери бота → **Bot Settings → Menu Button** (или **Configure Mini App**).
2. Укажи URL: `https://ВАШ-домен.ru`

---

## Готово ✅

Открой бота в Telegram, напиши `/start` — кнопка «🚀 Открыть приложение»
запустит Mini App с твоего сервера. Работает 24/7, даже когда твой ПК выключен.

---

## Полезные команды на сервере

```bash
# перезапустить после изменений кода
systemctl restart customersdream

# посмотреть логи в реальном времени
journalctl -u customersdream -f

# обновить код (если через git)
cd /opt/CustomersDream && git pull && systemctl restart customersdream
```
