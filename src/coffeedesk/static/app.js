'use strict';
const API = '/ui-api';
const root = document.querySelector('#root');
const roles = {admin:'Администратор',operator:'Оператор',technician:'Исполнитель',applicant:'Заявитель'};
const priorities = {low:'Низкий',normal:'Обычный',high:'Высокий',urgent:'Срочный'};
const statuses = {new:'Новая',in_progress:'В работе',done:'Выполнена',closed:'Закрыта'};
const events = {created:'Создана заявка',seeded:'Учебные данные',updated:'Изменены реквизиты',assigned:'Назначен исполнитель',status_changed:'Изменён статус',archived:'Архивирована'};
let user = null, csrf = sessionStorage.getItem('coffee_csrf'), catalogs = null, generation = 0;
const e = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date = value => new Date(value).toLocaleString('ru-RU', {dateStyle:'short',timeStyle:'short'});
const manager = () => ['admin','operator'].includes(user?.role_code);
const creator = () => ['admin','operator','applicant'].includes(user?.role_code);
const badge = item => `<span class="badge ${e(item.status_code)}">${e(item.status_name)}</span>`;

async function api(path, method='GET', body) {
  const headers = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (csrf && method !== 'GET') headers['X-CSRF-Token'] = csrf;
  let response;
  try { response = await fetch(API + path, {method, headers, credentials:'same-origin', body:body === undefined ? undefined : JSON.stringify(body)}); }
  catch (_) { throw new Error('Нет связи с сервером. Проверьте подключение и повторите.'); }
  if (response.status === 204) return null;
  const result = await response.json();
  if (!response.ok) {
    if (response.status === 401 && path !== '/auth/login') {
      user = null; csrf = null; sessionStorage.removeItem('coffee_csrf'); location.hash = 'login';
    }
    let message = result.error?.message || 'Не удалось выполнить запрос.';
    if (result.error?.details?.length) message += ' Поля: ' + result.error.details.map(x => x.field.replace('body.','')).join(', ') + '.';
    throw new Error(message);
  }
  return result;
}

function toast(message) {
  const element = document.querySelector('#toast');
  element.textContent = message; element.classList.add('visible');
  window.setTimeout(() => element.classList.remove('visible'), 4000);
}
function navigate(hash) { if (location.hash === '#' + hash) render(); else location.hash = hash; }
function heading(title, sub, action='') {
  return `<div class="heading"><div><div class="eyebrow">Техническая служба</div><h1>${e(title)}</h1><p class="muted">${e(sub)}</p></div>${action}</div>`;
}
function shell(content, archive=false) {
  return `<div class="app"><aside><a class="brand" href="#requests">☕ Coffee<span>Desk</span></a><div class="tag">Забота о вашем баре</div><nav><a class="${archive?'':'active'}" href="#requests">▤ &nbsp; ${manager()?'Все заявки':user.role_code==='technician'?'Мои назначения':'Мои заявки'}</a>${creator()?'<a href="#new">＋ &nbsp; Создать заявку</a>':''}${user.role_code==='admin'?`<a class="${archive?'active':''}" href="#archive">◷ &nbsp; Архив заявок</a>`:''}<a href="/docs" target="_blank" rel="noopener">↗ &nbsp; API / Swagger</a></nav><small>Сервис начинается с деталей.<br>CoffeeDesk · учебный проект</small></aside><main class="workspace"><header><span>Рабочее пространство / ${archive?'Архив':'Заявки'}</span><div class="user"><span>${e(user.name.slice(0,2).toUpperCase())}</span><div>${e(user.name)}<br><small class="muted">${e(roles[user.role_code])}</small></div><button data-action="logout">Выйти</button></div></header>${content}<footer>COFFEEDESK / УЧЁТ ЗАЯВОК КОФЕ-БАРОВ · ДЕМОНСТРАЦИОННЫЕ ДАННЫЕ</footer></main></div>`;
}
function login() {
  return `<div class="login-wrap"><section class="login-story"><div class="brand">☕ Coffee<span>Desk</span></div><h1>Меньше поломок.<br>Больше хорошего<br>кофе.</h1><p>Единое пространство заботы о ваших кофе-барах. От первого обращения до решённой проблемы.</p><small>Система учёта заявок · CoffeeDesk</small></section><section class="login-form"><div class="card"><div class="eyebrow">С возвращением</div><h1>Вход в CoffeeDesk</h1><p class="muted">Используйте свою учётную запись.</p><form id="login-form"><div class="notice error form-error" role="alert"></div><div class="field"><label for="username">Логин</label><input id="username" name="username" required minlength="3" maxlength="50" autocomplete="username" placeholder="Ваш логин"></div><div class="field"><label for="password">Пароль</label><input id="password" name="password" type="password" required maxlength="200" autocomplete="current-password" placeholder="Введите пароль"></div><button class="primary" type="submit">Войти →</button></form><p class="muted" style="font-size:12px;margin-top:20px">Нет доступа? Обратитесь к администратору.<br>Тестовые пароли создаются локально и не публикуются.</p></div></section></div>`;
}
async function loadCatalogs() {
  if (!catalogs) {
    const [categories,cafes,users] = await Promise.all([api('/categories'),api('/cafes'),api('/users')]);
    catalogs = {categories,cafes,users};
  }
  return catalogs;
}
function options(items, selected) { return items.map(item => `<option value="${item.id}" ${String(item.id)===String(selected)?'selected':''}>${e(item.name)}</option>`).join(''); }
function dictionaryOptions(items, selected) { return Object.entries(items).map(([value,label]) => `<option value="${value}" ${value===selected?'selected':''}>${label}</option>`).join(''); }

async function list(params, archive) {
  const c = await loadCatalogs();
  const query = new URLSearchParams(params); query.set('archived', archive); query.set('limit',20);
  const items = await api('/requests?' + query);
  const active = items.filter(x => ['new','in_progress'].includes(x.status_code)).length;
  const content = heading(archive?'Архив заявок':'Заявки кофе-баров', archive?'Закрытые обращения с сохранённой историей.':'Всё, что нужно для бесперебойной работы.', creator()?'<a class="button primary" href="#new">＋ Создать заявку</a>':'') +
    `<div class="stats"><div class="stat">Открытые<strong>${active}</strong><small>В текущей выборке</small></div><div class="stat">В работе<strong>${items.filter(x=>x.status_code==='in_progress').length}</strong><small>Уже занимаемся решением</small></div><div class="stat">Выполнено<strong>${items.filter(x=>x.status_code==='done').length}</strong><small>В текущей выборке</small></div></div><div class="table-card"><form id="filters" class="filters"><div class="filter search"><label for="q">Поиск по номеру, теме или описанию</label><input id="q" name="q" maxlength="120" placeholder="Например, кран или CB-00001" value="${e(params.get('q'))}"></div><div class="filter"><label for="status-filter">Статус</label><select id="status-filter" name="status_code"><option value="">Все статусы</option>${dictionaryOptions(statuses,params.get('status_code'))}</select></div><div class="filter"><label for="category-filter">Категория</label><select id="category-filter" name="category_id"><option value="">Все категории</option>${options(c.categories,params.get('category_id'))}</select></div><div class="filter"><label for="cafe-filter">Кофе-бар</label><select id="cafe-filter" name="cafe_id"><option value="">Все бары</option>${options(c.cafes,params.get('cafe_id'))}</select></div><button type="submit">Найти</button></form>${items.length?`<div class="table-scroll"><table><thead><tr><th>Заявка</th><th>Статус</th><th>Приоритет</th><th>Исполнитель</th><th></th></tr></thead><tbody>${items.map(item => `<tr><td><span class="number">${e(item.number)}</span><strong><a href="#requests/${item.id}">${e(item.title)}</a></strong><small>${e(item.cafe_name)} · ${e(item.category_name)}</small></td><td>${badge(item)}</td><td class="${e(item.priority)}">${e(priorities[item.priority])}</td><td>${e(item.assignee_name||'Не назначен')}</td><td><a href="#requests/${item.id}" aria-label="Открыть ${e(item.number)}">→</a></td></tr>`).join('')}</tbody></table></div>`:'<div class="empty"><h2>Заявок не найдено</h2><p class="muted">Попробуйте другой запрос или сбросьте фильтры.</p><button data-action="reset-filters">Сбросить фильтры</button></div>'}<div class="foot"><span>Показано ${items.length} · страница ${Math.floor(Number(params.get('offset')||0)/20)+1}</span><div><button data-action="prev" ${Number(params.get('offset')||0)<=0?'disabled':''}>← Назад</button> <button data-action="next" ${items.length<20?'disabled':''}>Далее →</button></div></div></div>`;
  return shell(content,archive);
}
async function form(id) {
  const c = await loadCatalogs(), item = id?await api('/requests/'+id):null;
  return shell(heading(item?'Редактирование заявки':'Новая заявка',item?item.number+' · изменения сохранятся в истории.':'Расскажите о проблеме — мы поможем её решить.','<a class="button" href="#requests">← К списку</a>')+`<div class="card form"><form id="request-form" data-id="${id||''}"><div class="notice">Если ситуация аварийная, сначала свяжитесь с ответственным по телефону.</div><div class="notice error form-error" role="alert"></div><div class="field"><label for="title">Тема заявки *</label><input id="title" name="title" required minlength="3" maxlength="120" value="${e(item?.title)}" placeholder="Например: протекает кран у мойки"><small>Коротко опишите проблему · 3–120 символов</small></div><div class="grid"><div class="field"><label for="cafe">Кофе-бар *</label><select id="cafe" name="cafe_id" required>${options(c.cafes,item?.cafe_id)}</select></div><div class="field"><label for="category">Категория *</label><select id="category" name="category_id" required>${options(c.categories,item?.category_id)}</select></div></div><div class="field"><label for="description">Описание *</label><textarea id="description" name="description" required minlength="10" maxlength="4000" placeholder="Где возникла проблема, когда её заметили, как влияет на работу">${e(item?.description)}</textarea><small>10–4000 символов · не указывайте персональные данные</small></div><div class="field"><label for="priority">Приоритет</label><select id="priority" name="priority">${dictionaryOptions(priorities,item?.priority||'normal')}</select></div><div class="actions"><a class="button" href="${item?'#requests/'+id:'#requests'}">Отмена</a><button type="submit" class="primary">${item?'Сохранить изменения':'Создать заявку'}</button></div></form></div>`);
}
async function detail(id) {
  const [item,comments,history,c] = await Promise.all([api('/requests/'+id),api('/requests/'+id+'/comments'),api('/requests/'+id+'/history'),loadCatalogs()]);
  const editable = !item.archived && item.status_code!=='closed' && (manager() || (user.role_code==='applicant' && item.status_code==='new'));
  const next = {new:'in_progress',in_progress:'done',done:'closed'}[item.status_code];
  const canStatus = !item.archived && next && (manager() || (user.role_code==='technician' && next!=='closed'));
  const assignment = manager() && !item.archived && ['new','in_progress'].includes(item.status_code);
  const canArchive = user.role_code==='admin' && !item.archived && item.status_code==='closed';
  return shell(heading(item.title,item.number+' · создана '+date(item.created_at),editable?`<a class="button" href="#requests/${id}/edit">Редактировать</a>`:'<a class="button" href="#requests">← К списку</a>')+`<div class="notice error form-error" role="alert"></div><div class="two"><section><div class="card"><h2>Описание проблемы</h2><p class="body-text">${e(item.description)}</p>${badge(item)} ${item.archived?'<span class="badge closed">В архиве</span>':''}</div><div class="card stack"><h2>Обсуждение</h2>${comments.length?comments.map(x=>`<div class="comment"><b>${e(x.author_name)}</b><small> · ${date(x.created_at)}</small><p class="body-text">${e(x.body)}</p></div>`).join(''):'<p class="muted">Пока нет комментариев. Уточните детали обращения.</p>'}${!item.archived?`<form id="comment-form" data-id="${id}" class="stack"><label for="comment">Новый комментарий</label><textarea id="comment" name="body" required maxlength="2000" placeholder="Уточните детали или сообщите о результате"></textarea><button type="submit" class="primary stack">Отправить</button></form>`:''}</div><div class="card stack"><h2>История изменений</h2><div class="timeline">${history.map(x=>`<div>${date(x.created_at)} · ${e(x.actor_name)}<br>${e(events[x.event]||x.event)}${x.event==='status_changed'?': '+e(statuses[x.old_value]||x.old_value)+' → '+e(statuses[x.new_value]||x.new_value):''}</div>`).join('')}</div></div></section><section><div class="card"><h2>Детали заявки</h2><dl class="meta"><dt>Кофе-бар</dt><dd>${e(item.cafe_name)}</dd><dt>Категория</dt><dd>${e(item.category_name)}</dd><dt>Приоритет</dt><dd class="${e(item.priority)}">${e(priorities[item.priority])}</dd><dt>Заявитель</dt><dd>${e(item.applicant_name)}</dd><dt>Исполнитель</dt><dd>${e(item.assignee_name||'Не назначен')}</dd><dt>Обновлена</dt><dd>${date(item.updated_at)}</dd></dl>${assignment?`<form id="assign-form" data-id="${id}" class="stack"><label for="assignee">Назначение</label><select id="assignee" name="assignee_id">${item.status_code==='new'?'<option value="">Не назначен</option>':''}${options(c.users.filter(x=>x.role_code==='technician'&&x.active),item.assignee_id)}</select><button type="submit" class="stack">Назначить</button></form>`:''}</div>${canStatus||canArchive?`<div class="card stack"><h2>Управление</h2>${canStatus?`<button class="primary" data-action="status" data-id="${id}" data-status="${next}">${{in_progress:'Взять в работу',done:'Отметить выполнение',closed:'Закрыть заявку'}[next]}</button>`:''}${canArchive?`<button class="danger" data-action="archive" data-id="${id}" data-number="${e(item.number)}">Архивировать заявку</button>`:''}<p class="muted stack" style="font-size:12px">Новая → В работе → Выполнена → Закрыта. Для начала нужен исполнитель.</p></div>`:''}</section></div>`,item.archived);
}
async function render() {
  const current = ++generation;
  if (!user) { root.innerHTML=login(); return; }
  const [route,query=''] = (location.hash.slice(1)||'requests').split('?');
  const parts = route.split('/');
  root.innerHTML='<div class="loading" role="status">Загрузка…</div>';
  try {
    let content;
    if (route==='new') content=await form();
    else if (parts[0]==='requests' && parts[1]) content=parts[2]==='edit'?await form(Number(parts[1])):await detail(Number(parts[1]));
    else content=await list(new URLSearchParams(query),route==='archive');
    if (generation===current && user) { root.innerHTML=content; window.scrollTo(0,0); }
  } catch (error) {
    if (generation===current) root.innerHTML=user?shell(heading('Не удалось открыть страницу','Проверьте данные или повторите запрос.')+`<div class="notice error" role="alert">${e(error.message)}</div><a href="#requests" class="button">К списку</a> <button data-action="retry">Повторить</button>`):login();
  }
}
function showError(error) {
  const region=root.querySelector('.form-error');
  if (region) { region.textContent=error.message; region.scrollIntoView({block:'nearest'}); } else toast(error.message);
}
root.addEventListener('submit', async event => {
  event.preventDefault(); const f=event.target, button=f.querySelector('button[type="submit"]');
  if (button) button.disabled=true;
  try {
    const data=Object.fromEntries(new FormData(f));
    if (f.id==='login-form') {
      const result=await api('/auth/login','POST',data); user=result.user; csrf=result.csrf_token;
      sessionStorage.setItem('coffee_csrf',csrf); catalogs=null; navigate('requests');
    } else if (f.id==='filters') {
      const query=new URLSearchParams(Object.entries(data).filter(([,v])=>v));
      navigate((location.hash.startsWith('#archive')?'archive':'requests')+'?'+query);
    } else if (f.id==='request-form') {
      data.cafe_id=Number(data.cafe_id); data.category_id=Number(data.category_id);
      const item=await api('/requests'+(f.dataset.id?'/'+f.dataset.id:''),f.dataset.id?'PATCH':'POST',data);
      toast(f.dataset.id?'Изменения сохранены':'Заявка '+item.number+' создана'); navigate('requests/'+item.id);
    } else if (f.id==='comment-form') { await api('/requests/'+f.dataset.id+'/comments','POST',data); toast('Комментарий добавлен'); await render(); }
    else if (f.id==='assign-form') { await api('/requests/'+f.dataset.id+'/assignment','PATCH',{assignee_id:data.assignee_id?Number(data.assignee_id):null}); toast('Назначение сохранено'); await render(); }
  } catch(error) { showError(error); }
  finally { if (button) button.disabled=false; }
});
root.addEventListener('click',async event => {
  const button=event.target.closest('[data-action]'); if(!button)return;
  button.disabled=true;
  try {
    const action=button.dataset.action;
    if(action==='logout') { await api('/auth/logout','POST'); user=null;csrf=null;catalogs=null;sessionStorage.removeItem('coffee_csrf');navigate('login'); }
    else if(action==='status') { await api('/requests/'+button.dataset.id+'/status','PATCH',{status_code:button.dataset.status});toast('Статус изменён');await render(); }
    else if(action==='archive') {
      const dialog=document.querySelector('#confirm'); document.querySelector('#confirm-title').textContent='Архивировать '+button.dataset.number+'?';
      document.querySelector('#confirm-text').textContent='Заявка исчезнет из рабочего списка. История и комментарии сохранятся.';
      dialog.returnValue=''; dialog.showModal();
      const result=await new Promise(resolve=>dialog.addEventListener('close',()=>resolve(dialog.returnValue),{once:true}));
      if(result==='confirm') { await api('/requests/'+button.dataset.id+'?confirm=true','DELETE');toast('Заявка архивирована');navigate('archive'); }
    } else if(action==='retry') await render();
    else if(action==='reset-filters') navigate(location.hash.startsWith('#archive')?'archive':'requests');
    else if(action==='next'||action==='prev') {
      const [route,query='']=location.hash.slice(1).split('?'), params=new URLSearchParams(query);
      params.set('offset',Math.max(0,Number(params.get('offset')||0)+(action==='next'?20:-20)));navigate(route+'?'+params);
    }
  } catch(error) { showError(error); } finally { button.disabled=false; }
});
window.addEventListener('hashchange',render);
(async()=>{ if(csrf) {try{user=await api('/auth/me');}catch(_){user=null;}} await render(); })();
