/* Customers Dream — Telegram Mini App */

const API = '/api';
let userId = 0;
let history = [];
let currentCategoryId = null;
let currentCategoryEmoji = '';

// --- Telegram WebApp init ---
const tg = window.Telegram?.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
    tg.setHeaderColor('#0f0f1a');
    tg.setBackgroundColor('#0f0f1a');
    const user = tg.initDataUnsafe?.user;
    if (user) {
        userId = user.id;
        initUser(user);
    }
}

async function initUser(user) {
    try {
        const params = new URLSearchParams({
            user_id: user.id,
            username: user.username || '',
            first_name: user.first_name || '',
            last_name: user.last_name || '',
        });
        await fetch(`${API}/user/init?${params}`, { method: 'POST' });
    } catch (e) { /* silent */ }
}

// --- Landing ---
function goToHome() {
    pushHistory('landing', {});
    navigateTo('home');
    loadCategories();
}

function goToRequest(prefill = '') {
    pushHistory('landing', {});
    navigateTo('request', { prefill });
}

// --- Navigation ---
function navigateTo(page, data = {}) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const target = document.getElementById(`page-${page}`);
    if (target) target.classList.add('active');

    const backBtn = document.getElementById('btn-back');
    const title = document.getElementById('header-title');

    if (page === 'landing') {
        backBtn.classList.add('hidden');
        title.textContent = 'Customers Dream';
        history = [];
    } else {
        backBtn.classList.remove('hidden');
    }

    if (page === 'home') title.textContent = 'Бизнес-модели';

    // Update nav bar active state
    document.querySelectorAll('.nav-bar__item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === page);
    });

    if (page === 'subcategories') loadSubcategories(data.categoryId, data.categoryName, data.emoji);
    if (page === 'mockups') loadMockups(data.subId, data.subName);
    if (page === 'mockup-detail') loadMockupDetail(data.mockupId);
    if (page === 'favorites') loadFavorites();
    if (page === 'contact') setupContact();
    if (page === 'request') setupRequest(data.prefill || '');
}

function pushHistory(page, data) {
    history.push({ page, data });
}

function goBack() {
    if (history.length > 0) {
        const prev = history.pop();
        navigateTo(prev.page, prev.data);
    } else {
        navigateTo('landing');
    }
}

// --- Load Categories ---
async function loadCategories() {
    const grid = document.getElementById('categories-grid');
    grid.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const res = await fetch(`${API}/categories`);
        const categories = await res.json();
        grid.innerHTML = '';

        categories.forEach(cat => {
            const item = document.createElement('div');
            item.className = 'grid__item';
            item.onclick = () => {
                pushHistory('home', {});
                navigateTo('subcategories', { categoryId: cat.id, categoryName: cat.name, emoji: cat.emoji });
            };
            item.innerHTML = `
                <div class="grid__icon">${cat.emoji || '📁'}</div>
                <span class="grid__label">${cat.name}</span>
            `;
            grid.appendChild(item);
        });
    } catch (e) {
        grid.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:20px;">Не удалось загрузить каталог</p>';
    }
}

// --- Load Subcategories ---
async function loadSubcategories(categoryId, categoryName, emoji) {
    currentCategoryId = categoryId;
    currentCategoryEmoji = emoji || '📁';
    const list = document.getElementById('subcategories-list');
    const title = document.getElementById('sub-title');
    const headerTitle = document.getElementById('header-title');

    title.textContent = `${emoji || '📁'} ${categoryName}`;
    headerTitle.textContent = categoryName;
    list.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const res = await fetch(`${API}/categories/${categoryId}/subcategories`);
        const subs = await res.json();
        list.innerHTML = '';

        if (subs.length === 0) {
            list.innerHTML = '<div class="empty-state"><span class="empty-state__icon">📭</span><p>Скоро здесь появятся макеты</p></div>';
        } else {
            subs.forEach(sub => {
                const item = document.createElement('div');
                item.className = 'list__item';
                item.onclick = () => {
                    pushHistory('subcategories', { categoryId, categoryName, emoji });
                    navigateTo('mockups', { subId: sub.id, subName: sub.name });
                };
                item.innerHTML = `
                    <div class="list__item-icon">${currentCategoryEmoji}</div>
                    <div class="list__item-content">
                        <div class="list__item-title">${sub.name}</div>
                        <div class="list__item-subtitle">${sub.mockup_count} макет${pluralize(sub.mockup_count)}</div>
                    </div>
                    <div class="list__item-arrow">›</div>
                `;
                list.appendChild(item);
            });
        }

        // Always show request CTA at the bottom
        const cta = document.createElement('div');
        cta.className = 'request-cta';
        cta.innerHTML = `
            <p>Не нашёл нужное? Опиши — мы сделаем под тебя.</p>
            <button class="btn btn--primary btn--full" onclick="submitCustomRequest('${escapeStr(categoryName)}')">📝 Подать заявку</button>
        `;
        list.appendChild(cta);
    } catch (e) {
        list.innerHTML = '<p style="color:var(--text-muted);text-align:center;">Ошибка загрузки</p>';
    }
}

function submitCustomRequest(categoryName) {
    pushHistory('subcategories', { categoryId: currentCategoryId, categoryName, emoji: currentCategoryEmoji });
    navigateTo('request', { prefill: categoryName });
}

// --- Load Mockups ---
async function loadMockups(subId, subName) {
    const list = document.getElementById('mockups-list');
    const title = document.getElementById('mockups-title');
    const headerTitle = document.getElementById('header-title');

    title.textContent = subName;
    headerTitle.textContent = subName;
    list.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const res = await fetch(`${API}/subcategories/${subId}/mockups?user_id=${userId}`);
        const mockups = await res.json();
        list.innerHTML = '';

        if (mockups.length === 0) {
            list.innerHTML = `
                <div class="empty-state">
                    <span class="empty-state__icon">🖼</span>
                    <p>Макеты скоро появятся</p>
                </div>
                <div class="request-cta">
                    <p>Хочешь макет в этой категории? Подай заявку — сделаем для тебя.</p>
                    <button class="btn btn--primary btn--full" onclick="submitCustomRequest('${escapeStr(subName)}')">📝 Подать заявку</button>
                </div>
            `;
            return;
        }

        mockups.forEach(m => renderMockupCard(m, list, subId, subName));

        // CTA after mockups too
        const cta = document.createElement('div');
        cta.className = 'request-cta';
        cta.innerHTML = `
            <p>Хочешь что-то другое? Опиши свою идею.</p>
            <button class="btn btn--primary btn--full" onclick="submitCustomRequest('${escapeStr(subName)}')">📝 Подать заявку</button>
        `;
        list.appendChild(cta);
    } catch (e) {
        list.innerHTML = '<p style="color:var(--text-muted);text-align:center;">Ошибка загрузки</p>';
    }
}

function renderMockupCard(m, container, subId, subName) {
    const card = document.createElement('div');
    card.className = 'mockup-card';
    card.onclick = () => {
        if (subId) pushHistory('mockups', { subId, subName });
        else pushHistory('favorites', {});
        navigateTo('mockup-detail', { mockupId: m.id });
    };

    const price = m.price_cents
        ? `${(m.price_cents / 100).toFixed(0)} ${m.currency || 'USD'}`
        : 'По запросу';

    const imageContent = m.photo_url
        ? `<img src="${m.photo_url}" alt="${m.title}" loading="lazy">`
        : `<span>🖼</span>`;

    card.innerHTML = `
        <div class="mockup-card__image">${imageContent}</div>
        <div class="mockup-card__body">
            <div class="mockup-card__title">${m.title}</div>
            <div class="mockup-card__meta">
                <span class="mockup-card__price">${price}</span>
                <span class="mockup-card__like">${m.is_liked ? '❤️' : '🤍'}</span>
            </div>
        </div>
    `;
    container.appendChild(card);
}

// --- Mockup Detail ---
async function loadMockupDetail(mockupId) {
    const container = document.getElementById('mockup-detail');
    const headerTitle = document.getElementById('header-title');
    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const res = await fetch(`${API}/mockups/${mockupId}?user_id=${userId}`);
        const m = await res.json();
        headerTitle.textContent = m.title;

        const price = m.price_cents
            ? `${(m.price_cents / 100).toFixed(0)} ${m.currency || 'USD'}`
            : 'Стоимость по запросу';

        const imageContent = m.photo_url
            ? `<img src="${m.photo_url}" alt="${m.title}">`
            : `<div class="mockup-detail__placeholder">🖼</div>`;

        let featuresHtml = '';
        if (m.features) {
            const featureList = m.features.split('\n').filter(f => f.trim());
            featuresHtml = `
                <div class="mockup-detail__features">
                    <h3>Что включено</h3>
                    <ul>${featureList.map(f => `<li>${f.trim()}</li>`).join('')}</ul>
                </div>
            `;
        }

        let figmaBtn = '';
        if (m.figma_link) {
            figmaBtn = `<a href="${m.figma_link}" target="_blank" class="btn btn--outline btn--sm">🔗 Figma</a>`;
        }

        container.innerHTML = `
            <div class="mockup-detail__image">${imageContent}</div>
            <h2 class="mockup-detail__title">${m.title}</h2>
            <p class="mockup-detail__path">${m.category_name || ''} → ${m.subcategory_name || ''}</p>
            ${m.description ? `<p class="mockup-detail__description">${m.description}</p>` : ''}
            ${featuresHtml}
            <div class="mockup-detail__price">${price}</div>
            <div class="mockup-detail__actions">
                <button class="btn btn--primary" style="flex:1" onclick="contactAboutMockup(${m.id}, '${escapeStr(m.title)}')">💬 Хочу этот сайт</button>
                <button class="btn btn--like ${m.is_liked ? 'liked' : ''}" id="like-btn-${m.id}" onclick="toggleLike(${m.id}, event)">
                    ${m.is_liked ? '❤️' : '🤍'}
                </button>
            </div>
            ${figmaBtn}
        `;
    } catch (e) {
        container.innerHTML = '<div class="empty-state"><p>Ошибка загрузки макета</p></div>';
    }
}

// --- Like ---
async function toggleLike(mockupId, event) {
    if (event) event.stopPropagation();
    if (!userId) { showToast('Откройте бота через Telegram'); return; }

    try {
        const res = await fetch(`${API}/like/${mockupId}?user_id=${userId}`, { method: 'POST' });
        const data = await res.json();
        const btn = document.getElementById(`like-btn-${mockupId}`);
        if (btn) {
            btn.className = `btn btn--like ${data.liked ? 'liked' : ''}`;
            btn.innerHTML = data.liked ? '❤️' : '🤍';
        }
        showToast(data.liked ? 'Добавлено в избранное ❤️' : 'Убрано из избранного');
    } catch (e) {
        showToast('Ошибка');
    }
}

// --- Favorites ---
async function loadFavorites() {
    const list = document.getElementById('favorites-list');
    const empty = document.getElementById('favorites-empty');
    const headerTitle = document.getElementById('header-title');
    headerTitle.textContent = 'Избранное';

    list.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    empty.classList.add('hidden');

    if (!userId) {
        list.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }

    try {
        const res = await fetch(`${API}/favorites?user_id=${userId}`);
        const mockups = await res.json();
        list.innerHTML = '';

        if (mockups.length === 0) {
            empty.classList.remove('hidden');
            return;
        }

        mockups.forEach(m => renderMockupCard(m, list, null, null));
    } catch (e) {
        list.innerHTML = '<p style="color:var(--text-muted);text-align:center;">Ошибка загрузки</p>';
    }
}

// --- Request form ---
function setupRequest(prefill) {
    const headerTitle = document.getElementById('header-title');
    headerTitle.textContent = 'Подать заявку';
    const businessInput = document.getElementById('request-business');
    if (prefill && businessInput) {
        businessInput.value = prefill;
    }
}

document.getElementById('btn-send-request').addEventListener('click', async () => {
    const business = document.getElementById('request-business').value.trim();
    const features = document.getElementById('request-features').value.trim();
    const budget = document.getElementById('request-budget').value.trim();
    const contactInfo = document.getElementById('request-contact-info').value.trim();

    if (!business) { showToast('Укажи тип бизнеса'); return; }
    if (!features) { showToast('Опиши фичи кратко'); return; }

    const message = [
        `🏢 Бизнес: ${business}`,
        `⚙️ Фичи: ${features}`,
        budget ? `💰 Бюджет: ${budget}` : '',
        contactInfo ? `📞 Контакт: ${contactInfo}` : '',
    ].filter(Boolean).join('\n');

    try {
        const res = await fetch(`${API}/contact?user_id=${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, request_type: 'custom' }),
        });
        if (res.ok) {
            showToast('Заявка отправлена! ✅');
            document.getElementById('request-business').value = '';
            document.getElementById('request-features').value = '';
            document.getElementById('request-budget').value = '';
            document.getElementById('request-contact-info').value = '';
        } else {
            showToast('Ошибка отправки');
        }
    } catch (e) {
        showToast('Ошибка сети');
    }
});

// --- Contact (about specific mockup) ---
function setupContact() {
    const headerTitle = document.getElementById('header-title');
    headerTitle.textContent = 'Связаться';
    const managerLink = document.getElementById('btn-manager-link');
    managerLink.href = 'https://t.me/il1aLis';
}

function contactAboutMockup(mockupId, title) {
    pushHistory('mockup-detail', { mockupId });
    navigateTo('contact');
    const textarea = document.getElementById('contact-message');
    textarea.value = `Привет! Меня интересует макет "${title}" (ID: ${mockupId}). Расскажите подробнее о стоимости и сроках.`;
}

document.getElementById('btn-send-contact').addEventListener('click', async () => {
    const message = document.getElementById('contact-message').value.trim();
    if (!message) { showToast('Напиши сообщение'); return; }
    if (!userId) { showToast('Откройте бота через Telegram'); return; }

    try {
        const res = await fetch(`${API}/contact?user_id=${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
        });
        if (res.ok) {
            showToast('Заявка отправлена! ✅');
            document.getElementById('contact-message').value = '';
        } else {
            showToast('Ошибка отправки');
        }
    } catch (e) {
        showToast('Ошибка сети');
    }
});

// --- Utils ---
function pluralize(n) {
    if (n % 10 === 1 && n % 100 !== 11) return '';
    if (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20)) return 'а';
    return 'ов';
}

function escapeStr(s) {
    return (s || '').replace(/'/g, "\\'").replace(/"/g, '\\"');
}

function showToast(text) {
    let toast = document.querySelector('.toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    toast.textContent = text;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2500);
}

// --- Event listeners ---
document.getElementById('btn-back').addEventListener('click', goBack);

document.querySelectorAll('.nav-bar__item').forEach(item => {
    item.addEventListener('click', () => {
        const page = item.dataset.page;
        if (page) {
            history = [];
            navigateTo(page);
            if (page === 'home') loadCategories();
        }
    });
});

// No auto-load on init — landing is the first screen
