/* Customers Dream — Mini App v4 */

const API = '/api';
let userId = 0;
let navHistory = [];
let currentTab = 'home';
let allCategories = [];
let userInfo = {};
let activeFilters = { platform: '', complexity: '', price: '' };
// Language resolved after Telegram init (see below). 'ru' or 'en'.
let lang = 'en';

// Gradient palette for mockup thumbnails
const GRADIENTS = [
    'linear-gradient(135deg,#7b2ff7,#f107a3)',
    'linear-gradient(135deg,#2bd2ff,#7b2ff7)',
    'linear-gradient(135deg,#ff8a00,#f107a3)',
    'linear-gradient(135deg,#00c6ff,#0072ff)',
    'linear-gradient(135deg,#f7971e,#ffd200)',
    'linear-gradient(135deg,#ee0979,#ff6a00)',
    'linear-gradient(135deg,#11998e,#38ef7d)',
    'linear-gradient(135deg,#8e2de2,#4a00e0)',
];
function gradientFor(str) {
    let h = 0;
    for (let i = 0; i < (str || '').length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0;
    return GRADIENTS[h % GRADIENTS.length];
}

const PLATFORM_LABEL = { site: '🌐 Сайт', bot: '🤖 Бот', app: '📱 Приложение' };
const COMPLEXITY_LABEL = { simple: '⚡ Простой', medium: '🔧 Средний', complex: '🚀 Сложный' };

// Real Figma-style preview per category (matched by keyword in category name)
const CATEGORY_PREVIEWS = [
    { kw: 'крипт', img: '/assets/mockups/crypto.png' },
    { kw: 'финанс', img: '/assets/mockups/crypto.png' },
    { kw: 'казино', img: '/assets/mockups/casino.png' },
    { kw: 'гембл', img: '/assets/mockups/casino.png' },
    { kw: 'маркетплейс', img: '/assets/mockups/market.png' },
    { kw: 'ресторан', img: '/assets/mockups/food.png' },
    { kw: 'кафе', img: '/assets/mockups/food.png' },
    { kw: 'образован', img: '/assets/mockups/edu.png' },
    { kw: 'бьюти', img: '/assets/mockups/beauty.png' },
    { kw: 'спа', img: '/assets/mockups/beauty.png' },
    { kw: 'фитнес', img: '/assets/mockups/fitness.png' },
    { kw: 'спорт', img: '/assets/mockups/fitness.png' },
    { kw: 'медиц', img: '/assets/mockups/medical.png' },
    { kw: 'клиник', img: '/assets/mockups/medical.png' },
    { kw: 'тревел', img: '/assets/mockups/travel.png' },
    { kw: 'туризм', img: '/assets/mockups/travel.png' },
    { kw: 'авто', img: '/assets/mockups/auto.png' },
    { kw: 'недвиж', img: '/assets/mockups/realestate.png' },
    { kw: 'услуг', img: '/assets/mockups/services.png' },
    { kw: 'сервис', img: '/assets/mockups/services.png' },
];
function previewFor(categoryName) {
    const lower = (categoryName || '').toLowerCase();
    const hit = CATEGORY_PREVIEWS.find(p => lower.includes(p.kw));
    return hit ? hit.img : null;
}

// --- i18n ---
const I18N = {
    ru: {
        appName: 'Customers Dream', catalog: 'Каталог', myProjects: 'Мои проекты',
        catalogSub: 'Готовые макеты по категориям', customSub: 'Индивидуальная разработка под тебя',
        mockups: 'макетов', cats: 'категорий', support: 'поддержка',
        navHome: 'Главная', navFav: 'Избранное', navChat: 'Чат', navProfile: 'Профиль',
        favorites: 'Избранное', chat: 'Чат', profile: 'Профиль',
        balance: 'Баланс', referral: 'Реферальная программа', settings: 'Настройки',
        terms: 'Правила использования', langTitle: 'Язык', themeTitle: 'Тема',
        chatHeading: 'Чат с менеджером',
        chatDesc: 'Задай вопрос или опиши идею — наш менеджер свяжется с тобой в Telegram.',
        contactHeading: 'Хочу этот проект',
        contactTitleBar: 'Хочу проект',
        contactDesc: 'Расскажи детали — наш менеджер свяжется с тобой в Telegram.',
    },
    en: {
        appName: 'Customers Dream', catalog: 'Catalog', myProjects: 'My projects',
        catalogSub: 'Ready-made templates by category', customSub: 'Custom development for you',
        mockups: 'templates', cats: 'categories', support: 'support',
        navHome: 'Home', navFav: 'Saved', navChat: 'Chat', navProfile: 'Profile',
        favorites: 'Saved', chat: 'Chat', profile: 'Profile',
        balance: 'Balance', referral: 'Referral program', settings: 'Settings',
        terms: 'Terms of use', langTitle: 'Language', themeTitle: 'Theme',
        chatHeading: 'Chat with manager',
        chatDesc: 'Ask a question or describe your idea — our manager will contact you in Telegram.',
        contactHeading: 'I want this project',
        contactTitleBar: 'I want a project',
        contactDesc: 'Share the details — our manager will contact you in Telegram.',
    },
};
function t(key) { return (I18N[lang] && I18N[lang][key]) || I18N.ru[key] || key; }

// --- Telegram init ---
const tg = window.Telegram?.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
    const user = tg.initDataUnsafe?.user;
    if (user) { userId = user.id; userInfo = user; initUser(user); }
}

// Always make sure we have a usable user id so favorites / requests work even
// when Telegram doesn't pass init data (e.g. opened outside a web_app button).
// Real Telegram users keep their real id; everyone else gets a persistent
// anonymous id stored locally.
(function resolveUserId() {
    if (userId) return;
    let id = localStorage.getItem('cd_uid');
    if (!id) {
        id = String(7000000000 + Math.floor(Math.random() * 999999999));
        localStorage.setItem('cd_uid', id);
    }
    userId = Number(id);
})();

// Resolve default language:
//  1) explicit user choice from previous session,
//  2) Telegram's language_code,
//  3) the Telegram client / device language (navigator.language) — this is what
//     reflects "Telegram is set to Russian" even when initData isn't passed,
//  4) English fallback.
(function resolveLang() {
    const saved = localStorage.getItem('cd_lang');
    if (saved === 'ru' || saved === 'en') { lang = saved; return; }
    const tgLang = (tg?.initDataUnsafe?.user?.language_code || '').toLowerCase();
    const navLang = (navigator.language || navigator.userLanguage || '').toLowerCase();
    const detected = tgLang || navLang;
    lang = detected.startsWith('ru') ? 'ru' : 'en';
})();

async function initUser(user) {
    try {
        const params = new URLSearchParams({
            user_id: user.id, username: user.username || '',
            first_name: user.first_name || '', last_name: user.last_name || '',
        });
        await fetch(`${API}/user/init?${params}`, { method: 'POST' });
    } catch (e) {}
}

// --- Theme ---
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('cd_theme', theme);
    const bg = theme === 'light' ? '#f3f0fb' : '#0c0a18';
    if (tg) { try { tg.setHeaderColor(bg); tg.setBackgroundColor(bg); } catch (e) {} }
    document.querySelectorAll('#seg-theme .seg__btn').forEach(b =>
        b.classList.toggle('active', b.dataset.theme === theme));
}

// --- Language ---
function applyLang(l) {
    lang = l;
    localStorage.setItem('cd_lang', l);
    document.querySelectorAll('#seg-lang .seg__btn').forEach(b =>
        b.classList.toggle('active', b.dataset.lang === l));
    // Static labels
    const navMap = { home: 'navHome', favorites: 'navFav', chat: 'navChat', profile: 'navProfile' };
    document.querySelectorAll('.nav-bar__item').forEach(i =>
        i.querySelector('.nav-bar__label').textContent = t(navMap[i.dataset.tab]));
    document.querySelector('#btn-go-catalog .landing-btn__text strong').textContent = t('catalog');
    document.querySelector('#btn-go-catalog .landing-btn__text small').textContent = t('catalogSub');
    document.querySelector('#btn-go-custom .landing-btn__text strong').textContent = t('myProjects');
    document.querySelector('#btn-go-custom .landing-btn__text small').textContent = t('customSub');
    document.getElementById('home-stat-mockups').nextElementSibling.textContent = t('mockups');
    document.getElementById('home-stat-cats').nextElementSibling.textContent = t('cats');
    // Profile section titles
    const titles = document.querySelectorAll('#page-profile .profile-section__title');
    if (titles[0]) titles[0].textContent = t('balance');
    if (titles[1]) titles[1].textContent = t('referral');
    if (titles[2]) titles[2].textContent = t('settings');
    // Chat & contact pages
    const setText = (id, key) => { const el = document.getElementById(id); if (el) el.textContent = t(key); };
    setText('chat-desc', 'chatDesc');
    setText('contact-desc', 'contactDesc');
    if (currentTab === 'home') document.getElementById('header-title').textContent = t('appName');
}

// --- Banner carousel ---
const BANNERS = [
    { title: 'Создай бизнес сегодня', sub: 'Готовые сайты, боты и приложения', emoji: '🚀', grad: 'linear-gradient(135deg,#7b2ff7,#f107a3)', action: 'catalog' },
    { title: 'Запусти за 1 день', sub: 'Бери готовое решение и зарабатывай', emoji: '⚡', grad: 'linear-gradient(135deg,#ff8a00,#f107a3)', action: 'catalog' },
    { title: 'Нужно своё?', sub: 'Сделаем индивидуальный проект под тебя', emoji: '🎨', grad: 'linear-gradient(135deg,#2bd2ff,#7b2ff7)', action: 'custom' },
];
let bannerIndex = 0;
let bannerTimer = null;

function initBanner() {
    const track = document.getElementById('banner-track');
    const dots = document.getElementById('banner-dots');
    track.innerHTML = '';
    dots.innerHTML = '';
    BANNERS.forEach((b, i) => {
        const slide = document.createElement('div');
        slide.className = 'banner__slide';
        slide.style.background = b.grad;
        slide.innerHTML = `
            <div class="banner__slide-title">${b.title}</div>
            <div class="banner__slide-sub">${b.sub}</div>
            <div class="banner__slide-emoji">${b.emoji}</div>
        `;
        slide.onclick = () => b.action === 'custom' ? showCustomDev('') : showCatalog();
        track.appendChild(slide);
        const dot = document.createElement('div');
        dot.className = 'banner__dot' + (i === 0 ? ' active' : '');
        dots.appendChild(dot);
    });
    startBannerAuto();
}

function setBanner(i) {
    bannerIndex = (i + BANNERS.length) % BANNERS.length;
    document.getElementById('banner-track').style.transform = `translateX(-${bannerIndex * 100}%)`;
    document.querySelectorAll('.banner__dot').forEach((d, idx) =>
        d.classList.toggle('active', idx === bannerIndex));
}
function startBannerAuto() {
    clearInterval(bannerTimer);
    bannerTimer = setInterval(() => setBanner(bannerIndex + 1), 3500);
}

// --- Tabs ---
function switchTab(tab) {
    currentTab = tab;
    navHistory = [];
    updateBackButton();
    document.querySelectorAll('.nav-bar__item').forEach(i => i.classList.toggle('active', i.dataset.tab === tab));

    if (tab === 'home') { showPage('home-landing'); document.getElementById('header-title').textContent = t('appName'); }
    else if (tab === 'favorites') { showPage('favorites'); document.getElementById('header-title').textContent = t('favorites'); loadFavorites(); }
    else if (tab === 'chat') { showPage('chat'); document.getElementById('header-title').textContent = t('chat'); setupChat(); }
    else if (tab === 'profile') { showPage('profile'); document.getElementById('header-title').textContent = t('profile'); setupProfile(); }
}

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const el = document.getElementById(`page-${pageId}`);
    if (el) el.classList.add('active');
    updateBackButton();
}
function pushNav(pageId, data) {
    data = data || {};
    // If no explicit title given, capture whatever the header shows right now,
    // so returning to this page restores the correct title.
    if (!data.title) data.title = document.getElementById('header-title').textContent;
    navHistory.push({ pageId, data });
}
function updateBackButton() { document.getElementById('btn-back').classList.toggle('hidden', navHistory.length === 0); }

function goBack() {
    if (navHistory.length > 0) {
        const prev = navHistory.pop();
        showPage(prev.pageId);
        document.getElementById('header-title').textContent = prev.data.title || t('appName');
    } else {
        switchTab(currentTab);
    }
    updateBackButton();
}

// --- Catalog ---
function showCatalog() {
    pushNav('home-landing', { title: t('appName') });
    showPage('catalog');
    document.getElementById('header-title').textContent = t('catalog');
    loadCategories();
}
function showCustomDev(prefill) {
    pushNav('home-landing', { title: t('appName') });
    showPage('request');
    document.getElementById('header-title').textContent = t('myProjects');
    if (prefill) document.getElementById('request-business').value = prefill;
}

async function loadCategories() {
    const grid = document.getElementById('categories-grid');
    if (allCategories.length === 0) {
        grid.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
        try {
            const res = await fetch(`${API}/categories`);
            if (!res.ok) throw new Error('http ' + res.status);
            const data = await res.json();
            allCategories = Array.isArray(data) ? data : [];
        } catch (e) {
            allCategories = [];
            grid.innerHTML = '<div class="empty-state"><div class="empty-state__icon">⚠️</div><p>Не удалось загрузить каталог.<br>Перезапусти бота и попробуй снова.</p><button class="btn btn--primary" onclick="loadCategories()">Повторить</button></div>';
            return;
        }
    }
    renderCategories();
}

function renderCategories() {
    const grid = document.getElementById('categories-grid');
    grid.innerHTML = '';
    allCategories.forEach(cat => {
        const item = document.createElement('div');
        item.className = 'grid__item';
        item.onclick = () => openCategory(cat.id, cat.name);
        item.innerHTML = `
            <div class="grid__emoji">${cat.emoji || '📦'}</div>
            <span class="grid__label">${cat.name}</span>
        `;
        grid.appendChild(item);
    });
}

// --- Filters ---
function setupFilters() {
    document.querySelectorAll('#filters-bar .chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const group = chip.dataset.group;
            const value = chip.dataset.value;
            if (group === 'platform' && value === '') {
                activeFilters = { platform: '', complexity: '', price: '' };
            } else {
                activeFilters[group] = activeFilters[group] === value ? '' : value;
            }
            updateChipStates();
            applyFilters();
        });
    });
}

function updateChipStates() {
    const noFilter = !activeFilters.platform && !activeFilters.complexity && !activeFilters.price;
    document.querySelectorAll('#filters-bar .chip').forEach(chip => {
        const group = chip.dataset.group;
        const value = chip.dataset.value;
        if (group === 'platform' && value === '') chip.classList.toggle('active', noFilter);
        else chip.classList.toggle('active', activeFilters[group] === value);
    });
}

async function applyFilters() {
    const grid = document.getElementById('categories-grid');
    const filtered = document.getElementById('filtered-mockups');
    const noFilter = !activeFilters.platform && !activeFilters.complexity && !activeFilters.price;

    if (noFilter) {
        grid.classList.remove('hidden');
        filtered.classList.add('hidden');
        return;
    }

    grid.classList.add('hidden');
    filtered.classList.remove('hidden');
    filtered.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    const params = new URLSearchParams({ user_id: userId });
    if (activeFilters.platform) params.set('platform', activeFilters.platform);
    if (activeFilters.complexity) params.set('complexity', activeFilters.complexity);
    if (activeFilters.price) {
        const [min, max] = activeFilters.price.split('-');
        params.set('price_min', min);
        params.set('price_max', max);
    }

    try {
        const res = await fetch(`${API}/mockups/all?${params}`);
        if (!res.ok) throw new Error('http ' + res.status);
        const mockups = await res.json();
        filtered.innerHTML = '';
        if (!Array.isArray(mockups) || mockups.length === 0) {
            filtered.innerHTML = '<div class="empty-state"><div class="empty-state__icon">🔍</div><p>Ничего не найдено</p></div>';
            return;
        }
        mockups.forEach(m => renderMockupCard(m, filtered));
    } catch (e) {
        filtered.innerHTML = '<div class="empty-state"><div class="empty-state__icon">⚠️</div><p>Не удалось загрузить.<br>Перезапусти бота и попробуй снова.</p></div>';
    }
}

// --- Subcategories ---
function openCategory(catId, catName) {
    pushNav('catalog', { title: t('catalog') });
    showPage('subcategories');
    document.getElementById('header-title').textContent = catName;
    loadSubcategories(catId, catName);
}

async function loadSubcategories(categoryId, categoryName) {
    const list = document.getElementById('subcategories-list');
    list.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    const cat = allCategories.find(c => c.id === categoryId);
    const emoji = cat?.emoji || '📦';

    try {
        const res = await fetch(`${API}/categories/${categoryId}/subcategories`);
        const subs = await res.json();
        list.innerHTML = '';
        if (subs.length === 0) {
            list.innerHTML = '<div class="empty-state"><p>Скоро появятся</p></div>';
        } else {
            subs.forEach(sub => {
                const item = document.createElement('div');
                item.className = 'list__item';
                item.onclick = () => openMockups(sub.id, sub.name, categoryName);
                item.innerHTML = `
                    <div class="list__item-emoji">${emoji}</div>
                    <div class="list__item-content">
                        <div class="list__item-title">${sub.name}</div>
                        <div class="list__item-subtitle">${sub.mockup_count} макет${pluralize(sub.mockup_count)}</div>
                    </div>
                    <div class="list__item-arrow">›</div>`;
                list.appendChild(item);
            });
        }
        const cta = document.createElement('div');
        cta.className = 'request-cta';
        cta.innerHTML = `<p>Не нашёл? Опиши — сделаем под тебя.</p>
            <button class="btn btn--primary btn--full btn--sm" onclick="showCustomDev('${escapeStr(categoryName)}')">Подать заявку</button>`;
        list.appendChild(cta);
    } catch (e) {
        list.innerHTML = '<div class="empty-state"><p>Ошибка</p></div>';
    }
}

// --- Mockups ---
function openMockups(subId, subName, catName) {
    pushNav('subcategories', { title: catName || '' });
    showPage('mockups');
    document.getElementById('header-title').textContent = subName;
    loadMockups(subId, subName);
}

async function loadMockups(subId, subName) {
    const list = document.getElementById('mockups-list');
    list.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    try {
        const res = await fetch(`${API}/subcategories/${subId}/mockups?user_id=${userId}`);
        const mockups = await res.json();
        list.innerHTML = '';
        if (mockups.length === 0) {
            list.innerHTML = `<div class="empty-state"><div class="empty-state__icon">🖼</div><p>Макеты скоро появятся</p></div>`;
            return;
        }
        mockups.forEach(m => renderMockupCard(m, list));
    } catch (e) {
        list.innerHTML = '<div class="empty-state"><p>Ошибка</p></div>';
    }
}

// Build an <img> for a mockup: prefer its own product image, fall back to the
// category preview if the product image is missing/broken, then to an emoji.
function mockupImageTag(m, emojiClass, lazy) {
    const product = m.photo_url;
    const fallback = previewFor(m.category_name);
    const src = product || fallback;
    if (!src) return `<div class="${emojiClass}">${catEmoji(m.category_name)}</div>`;
    const onerr = (product && fallback && product !== fallback)
        ? ` onerror="this.onerror=null;this.src='${fallback}'"` : '';
    return `<img src="${src}" alt="${escapeStr(m.title)}"${lazy ? ' loading="lazy"' : ''}${onerr}>`;
}

function renderMockupCard(m, container) {
    const card = document.createElement('div');
    card.className = 'mockup-card';
    card.onclick = () => openDetail(m.id);
    const price = m.price_cents ? `$${(m.price_cents / 100).toFixed(0)}` : 'По запросу';
    const grad = gradientFor(m.title || m.category_name);
    const badge = m.platform ? PLATFORM_LABEL[m.platform] : '';

    const image = mockupImageTag(m, 'mockup-card__image-emoji', true);

    card.innerHTML = `
        <div class="mockup-card__image" style="background:${grad}">
            ${badge ? `<span class="mockup-card__badge">${badge}</span>` : ''}
            ${image}
        </div>
        <div class="mockup-card__body">
            <div class="mockup-card__title">${m.title}</div>
            <div class="mockup-card__meta">
                <span class="mockup-card__price">${price}</span>
                <span class="mockup-card__like ${m.is_liked ? 'liked' : ''}" onclick="event.stopPropagation();toggleLikeInline(this,${m.id})">${m.is_liked ? '♥' : '♡'}</span>
            </div>
        </div>`;
    container.appendChild(card);
}

function catEmoji(name) {
    const c = allCategories.find(c => c.name === name);
    return c?.emoji || '🖼';
}

// --- Detail ---
function openDetail(mockupId) {
    pushNav(currentDetailBackPage(), {});
    showPage('mockup-detail');
    loadMockupDetail(mockupId);
}
function currentDetailBackPage() {
    const active = document.querySelector('.page.active');
    return active ? active.id.replace('page-', '') : 'catalog';
}

async function loadMockupDetail(mockupId) {
    const container = document.getElementById('mockup-detail');
    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    try {
        const res = await fetch(`${API}/mockups/${mockupId}?user_id=${userId}`);
        const m = await res.json();
        document.getElementById('header-title').textContent = m.title;
        const price = m.price_cents ? `$${(m.price_cents / 100).toFixed(0)}` : 'По запросу';
        const grad = gradientFor(m.title || m.category_name);
        const image = mockupImageTag(m, 'mockup-detail__image-emoji', false);

        let featuresHtml = '';
        if (m.features) {
            const fl = m.features.split('\n').filter(f => f.trim());
            featuresHtml = `<div class="mockup-detail__features"><h3>Что включено</h3><ul>${fl.map(f => `<li>${f.trim()}</li>`).join('')}</ul></div>`;
        }
        const tags = [];
        if (m.platform) tags.push(PLATFORM_LABEL[m.platform]);
        if (m.complexity) tags.push(COMPLEXITY_LABEL[m.complexity]);

        container.innerHTML = `
            <div class="mockup-detail__image" style="background:${grad}">${image}</div>
            <p class="mockup-detail__path">${m.category_name || ''} → ${m.subcategory_name || ''}</p>
            <div class="mockup-detail__tags">${tags.map(tg => `<span class="mockup-detail__tag">${tg}</span>`).join('')}</div>
            ${m.description ? `<p class="mockup-detail__description">${m.description}</p>` : ''}
            ${featuresHtml}
            <div class="mockup-detail__price gradient-text">${price}</div>
            <div class="mockup-detail__actions">
                <button class="btn btn--primary" style="flex:1" onclick="contactAbout(${m.id},'${escapeStr(m.title)}')">Хочу этот проект</button>
                <button class="btn btn--like ${m.is_liked ? 'liked' : ''}" id="like-btn-${m.id}" onclick="toggleLike(${m.id})">${m.is_liked ? '♥' : '♡'}</button>
            </div>
            ${m.figma_link ? `<a href="${m.figma_link}" target="_blank" class="btn btn--ghost btn--full btn--sm">Открыть в Figma</a>` : ''}`;
    } catch (e) {
        container.innerHTML = '<div class="empty-state"><p>Ошибка загрузки</p></div>';
    }
}

// --- Likes ---
async function toggleLike(mockupId) {
    if (!userId) { showToast('Откройте через Telegram'); return; }
    try {
        const res = await fetch(`${API}/like/${mockupId}?user_id=${userId}`, { method: 'POST' });
        const data = await res.json();
        const btn = document.getElementById(`like-btn-${mockupId}`);
        if (btn) { btn.className = `btn btn--like ${data.liked ? 'liked' : ''}`; btn.textContent = data.liked ? '♥' : '♡'; }
        showToast(data.liked ? 'Добавлено в избранное' : 'Убрано');
    } catch (e) { showToast('Ошибка'); }
}
async function toggleLikeInline(el, mockupId) {
    if (!userId) { showToast('Откройте через Telegram'); return; }
    try {
        const res = await fetch(`${API}/like/${mockupId}?user_id=${userId}`, { method: 'POST' });
        const data = await res.json();
        el.className = `mockup-card__like ${data.liked ? 'liked' : ''}`;
        el.textContent = data.liked ? '♥' : '♡';
        showToast(data.liked ? 'Добавлено' : 'Убрано');
    } catch (e) { showToast('Ошибка'); }
}

// --- Favorites ---
async function loadFavorites() {
    const list = document.getElementById('favorites-list');
    const empty = document.getElementById('favorites-empty');
    list.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    empty.classList.add('hidden');
    if (!userId) { list.innerHTML = ''; empty.classList.remove('hidden'); return; }
    try {
        const res = await fetch(`${API}/favorites?user_id=${userId}`);
        const mockups = await res.json();
        list.innerHTML = '';
        if (mockups.length === 0) { empty.classList.remove('hidden'); return; }
        mockups.forEach(m => renderMockupCard(m, list));
    } catch (e) { list.innerHTML = '<div class="empty-state"><p>Ошибка</p></div>'; }
}

// --- Chat ---
function setupChat() {
    const el = document.getElementById('chat-desc');
    if (el) el.textContent = t('chatDesc');
}
document.getElementById('btn-send-chat').addEventListener('click', () => sendMessage('chat-message', 'chat'));

// --- Profile ---
function setupProfile() {
    const nameEl = document.getElementById('profile-name');
    if (userInfo.first_name || userInfo.last_name) nameEl.textContent = `${userInfo.first_name || ''} ${userInfo.last_name || ''}`.trim();
    else if (userInfo.username) nameEl.textContent = `@${userInfo.username}`;
    if (userId) {
        document.getElementById('profile-id').textContent = `ID: ${userId}`;
        document.getElementById('referral-link').textContent = `https://t.me/CustomersDream_bot?start=ref_${userId}`;
    }
    fetch(`${API}/config`).then(r => r.json()).then(cfg => {
        document.getElementById('crypto-address').textContent = cfg.crypto_usdt_trc20 || 'Уточните у менеджера';
    }).catch(() => {});
}

document.getElementById('btn-topup').addEventListener('click', () => document.getElementById('topup-section').classList.toggle('hidden'));
document.getElementById('btn-copy-crypto').addEventListener('click', () => copyText(document.getElementById('crypto-address').textContent, 'Адрес скопирован'));
document.getElementById('btn-copy-ref').addEventListener('click', () => copyText(document.getElementById('referral-link').textContent, 'Ссылка скопирована'));
document.getElementById('menu-favorites').addEventListener('click', () => switchTab('favorites'));
document.getElementById('menu-chat').addEventListener('click', () => switchTab('chat'));
document.getElementById('menu-terms').addEventListener('click', () => {
    pushNav('profile', { title: t('profile') });
    showPage('terms');
    document.getElementById('header-title').textContent = t('terms');
});

document.querySelectorAll('#seg-lang .seg__btn').forEach(b => b.addEventListener('click', () => applyLang(b.dataset.lang)));
document.querySelectorAll('#seg-theme .seg__btn').forEach(b => b.addEventListener('click', () => applyTheme(b.dataset.theme)));

// --- Request ---
document.getElementById('btn-send-request').addEventListener('click', async () => {
    const business = document.getElementById('request-business').value.trim();
    const features = document.getElementById('request-features').value.trim();
    const budget = document.getElementById('request-budget').value.trim();
    const contact = document.getElementById('request-contact-info').value.trim();
    if (!business) { showToast('Укажи тип бизнеса'); return; }
    if (!features) { showToast('Опиши фичи'); return; }
    const message = [`Бизнес: ${business}`, `Фичи: ${features}`, budget ? `Бюджет: ${budget}` : '', contact ? `Контакт: ${contact}` : ''].filter(Boolean).join('\n');
    const ok = await postContact(message, 'custom');
    if (ok) ['request-business', 'request-features', 'request-budget', 'request-contact-info'].forEach(id => document.getElementById(id).value = '');
});

// --- Contact ---
function contactAbout(mockupId, title) {
    pushNav('mockup-detail', {});
    showPage('contact');
    document.getElementById('header-title').textContent = t('contactTitleBar');
    document.getElementById('contact-desc').textContent = t('contactDesc');
    document.getElementById('contact-message').value = `Интересует "${title}" (ID: ${mockupId}). Расскажите о стоимости и сроках.`;
}
document.getElementById('btn-send-contact').addEventListener('click', () => sendMessage('contact-message', 'general'));

// --- Shared send helpers ---
async function sendMessage(textareaId, type) {
    const el = document.getElementById(textareaId);
    const msg = el.value.trim();
    if (!msg) { showToast('Напиши сообщение'); return; }
    const ok = await postContact(msg, type);
    if (ok) el.value = '';
}

async function postContact(message, request_type) {
    const uid = userId || 0;
    if (!uid) { showToast('Откройте через Telegram'); return false; }
    try {
        const res = await fetch(`${API}/contact?user_id=${uid}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, request_type }),
        });
        if (res.ok) { showToast('Заявка отправлена ✅'); return true; }
        showToast('Ошибка отправки');
        return false;
    } catch (e) { showToast('Ошибка сети'); return false; }
}

// --- Utils ---
function pluralize(n) {
    if (n % 10 === 1 && n % 100 !== 11) return '';
    if (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20)) return 'а';
    return 'ов';
}
function escapeStr(s) { return (s || '').replace(/'/g, "\\'").replace(/"/g, '\\"'); }
function copyText(text, okMsg) {
    if (!text || text === '—' || text === 'Уточните у менеджера') { showToast('Недоступно'); return; }
    navigator.clipboard.writeText(text).then(() => showToast(okMsg)).catch(() => showToast('Не удалось'));
}
function showToast(text) {
    let toast = document.querySelector('.toast');
    if (!toast) { toast = document.createElement('div'); toast.className = 'toast'; document.body.appendChild(toast); }
    toast.textContent = text;
    toast.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(() => toast.classList.remove('show'), 2200);
}

// --- Home stats ---
async function loadHomeStats() {
    try {
        const res = await fetch(`${API}/categories`);
        allCategories = await res.json();
        document.getElementById('home-stat-cats').textContent = allCategories.length;
        const res2 = await fetch(`${API}/mockups/all`);
        const all = await res2.json();
        document.getElementById('home-stat-mockups').textContent = all.length;
    } catch (e) {}
}

// --- Init ---
document.getElementById('btn-back').addEventListener('click', goBack);
document.getElementById('btn-go-catalog').addEventListener('click', showCatalog);
document.getElementById('btn-go-custom').addEventListener('click', () => showCustomDev(''));
document.querySelectorAll('.nav-bar__item').forEach(item => item.addEventListener('click', () => switchTab(item.dataset.tab)));

applyTheme(localStorage.getItem('cd_theme') || 'dark');
applyLang(lang);
setupFilters();
initBanner();
loadHomeStats();
