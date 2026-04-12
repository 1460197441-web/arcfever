const crypto = require('crypto');
const cloud = require('wx-server-sdk');
const { invokeMockService } = require('./mock-data');
const { buildSeedData } = require('./seed-data');

const db = cloud.database();

const COLLECTIONS = {
  users: 'users',
  schools: 'schools',
  instruments: 'instruments',
  agreements: 'agreements',
  certifications: 'certifications',
  categories: 'categories',
  favorites: 'favorites',
  cartItems: 'cart_items',
  orders: 'orders',
  chats: 'chats',
  chatMessages: 'chat_messages',
  ratings: 'ratings',
  reports: 'reports',
  disputes: 'disputes',
  posts: 'posts',
  projects: 'projects',
  aiTasks: 'ai_tasks'
};

const VERIFIED_STATUSES = ['已认证', '已通过'];
const ADMIN_ROLES = ['平台管理员'];

const ADMIN_LOGIN_USERNAME = 'arcfever';
const ADMIN_LOGIN_PASSWORD_HASH = '29b8530f4725d2dd995db549dc127d5cf09974245c0a5d76d101a2d598d1123f';

const AI_TOOL_LIBRARY = {
  'trend-forecast': {
    toolName: '趋势预测引擎',
    summary: '基于已有样本和场景变量，平台给出一版可用于立项讨论的趋势判断。',
    metrics: [
      { label: '置信区间', value: '86%' },
      { label: '关键变量', value: '4 项' },
      { label: '建议动作', value: '3 条' }
    ],
    insights: [
      '建议优先补齐基线样本，再扩大外推范围。',
      '核心影响因子主要集中在载荷变化、温度漂移和样本分层。',
      '当前结果适合做方案筛选，不建议直接替代正式实验结论。'
    ]
  },
  'resource-match': {
    toolName: '科研资源匹配器',
    summary: '系统根据目标、学科和设备特征，给出更合适的仪器与合作对象建议。',
    metrics: [
      { label: '候选资源', value: '6 个' },
      { label: '高匹配项', value: '2 个' },
      { label: '匹配度', value: '91%' }
    ],
    insights: [
      '优先考虑支持远程实验且附带数据处理代码的团队。',
      '同城或同省资源能明显降低交接与物流风险。',
      '建议在下单前同步实验流程和结果交付格式。'
    ]
  },
  'data-diagnosis': {
    toolName: '数据诊断助手',
    summary: '系统对输入数据做快速结构化诊断，给出异常点与补采建议。',
    metrics: [
      { label: '异常点', value: '3 处' },
      { label: '缺失项', value: '2 类' },
      { label: '可用度', value: '78%' }
    ],
    insights: [
      '时间序列采样间隔不完全一致，建议先统一重采样。',
      '部分变量缺少校准说明，后续做横向比较会有偏差。',
      '如果补齐环境变量记录，模型稳定性会明显提升。'
    ]
  }
};

const LEGACY_AUTO_VERIFIED_PROFILE = {
  openid: 'mock-openid-001',
  name: '司艳文',
  phone: '13800138000',
  email: 'siyanwen@ouc.edu.cn',
  instituteId: '20260001',
  school: '中国海洋大学',
  college: '海洋地球科学学院',
  proofName: 'ouc-lab-proof.pdf'
};

function clone(data) {
  return JSON.parse(JSON.stringify(data));
}

function nowString() {
  return new Date().toISOString().slice(0, 16).replace('T', ' ');
}

function asPriceLabel(price) {
  return `¥${price} / 天`;
}

function validatePhone(phone) {
  return /^1\d{10}$/.test(phone);
}

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function dayDiff(startDate, endDate) {
  const start = new Date(startDate);
  const end = new Date(endDate);
  const diff = Math.ceil((end - start) / (24 * 60 * 60 * 1000)) + 1;
  return diff > 0 ? diff : 1;
}

function isVerifiedUser(user) {
  return VERIFIED_STATUSES.includes(user && user.status);
}

function isAdminUser(user) {
  return !!(user && (user.isAdmin === true || ADMIN_ROLES.includes(user.role)));
}

function ensureVerified(user, actionName) {
  if (!isVerifiedUser(user)) {
    throw new Error(`${actionName || '当前操作'}仅对已认证用户开放`);
  }
}

function ensureAdmin(user, actionName) {
  if (!isAdminUser(user)) {
    throw new Error(`${actionName || '当前操作'}仅对管理员开放`);
  }
}

function getCertificationPendingMessage(status) {
  if (['已认证', '已通过'].includes(status)) {
    return '你的科研身份已通过平台认证，可以发布仪器并发起真实交易。';
  }
  if (status === '待审核') {
    return '你的认证信息正在审核中，审核通过后会自动解锁完整交易能力。';
  }
  if (status === '已驳回') {
    return '你的认证申请已被驳回，请补充正确的学校 / 机构信息后重新提交。';
  }
  return '请先完成实名认证和学校 / 机构信息填写，认证通过后才可发布仪器、加入购物车和下单。';
}

function ensureNotOwnInstrument(instrument, user, actionName) {
  if (instrument && user && instrument.sellerId === user._id) {
    throw new Error(`${actionName || '当前操作'}不支持购买或咨询自己发布的仪器`);
  }
}

function buildUnverifiedUserData(user = {}) {
  return {
    name: '未认证用户',
    role: isAdminUser(user) ? user.role : '普通用户',
    phone: '',
    email: '',
    instituteId: '',
    school: '',
    college: '',
    proofName: '',
    status: '未认证',
    isAdmin: !!user.isAdmin
  };
}

function isLegacyAutoVerifiedUser(user) {
  if (!user || user.openid === LEGACY_AUTO_VERIFIED_PROFILE.openid) return false;
  return (
    isVerifiedUser(user) &&
    user.name === LEGACY_AUTO_VERIFIED_PROFILE.name &&
    user.phone === LEGACY_AUTO_VERIFIED_PROFILE.phone &&
    user.email === LEGACY_AUTO_VERIFIED_PROFILE.email &&
    user.instituteId === LEGACY_AUTO_VERIFIED_PROFILE.instituteId &&
    user.school === LEGACY_AUTO_VERIFIED_PROFILE.school &&
    user.college === LEGACY_AUTO_VERIFIED_PROFILE.college &&
    user.proofName === LEGACY_AUTO_VERIFIED_PROFILE.proofName
  );
}

function normalizeTradeModes(tradeModes, fallbackModes = ['租赁']) {
  const source = Array.isArray(tradeModes)
    ? tradeModes
    : String(tradeModes || '')
        .split(/[\u3001\uff0c,/\s]+/)
        .filter(Boolean);
  const modes = source.filter(
    (mode, index, list) => ['租赁', '出售'].includes(mode) && list.indexOf(mode) === index
  );
  return modes.length ? modes : clone(fallbackModes);
}

function normalizeTradeMode(instrument, tradeMode) {
  const modes = normalizeTradeModes(instrument.tradeModes, [instrument.defaultTradeMode || '租赁']);
  if (tradeMode && modes.includes(tradeMode)) return tradeMode;
  if (instrument.defaultTradeMode && modes.includes(instrument.defaultTradeMode)) {
    return instrument.defaultTradeMode;
  }
  return modes[0];
}

function normalizeDateSelection(instrument, startDate, endDate) {
  const dates = instrument.availableDates || [];
  const defaultStart = dates[0] || '2026-03-20';
  const start = startDate && dates.includes(startDate) ? startDate : defaultStart;
  let end = endDate && dates.includes(endDate) ? endDate : start;
  if (new Date(end) < new Date(start)) end = start;
  return { startDate: start, endDate: end };
}

function getInsurancePlanById(instrument, insurancePlanId) {
  const plans = instrument.insurancePlans || [];
  return plans.find((item) => item.id === insurancePlanId) || plans[0] || null;
}

async function hasCollectionData(name) {
  try {
    const res = await db.collection(name).limit(1).get();
    return !!(res.data && res.data.length);
  } catch (error) {
    return false;
  }
}

async function ensureCollectionExists(name) {
  try {
    await db.collection(name).limit(1).get();
  } catch (error) {
    const message = String(error && (error.errMsg || error.message || error));
    if (
      message.includes('database collection not exists') ||
      message.includes('Db or Table not exist') ||
      message.includes('ResourceNotFound')
    ) {
      await db.createCollection(name);
      return;
    }
    throw error;
  }
}

async function seedCollection(name, items) {
  if (!Array.isArray(items) || !items.length) return 0;
  await ensureCollectionExists(name);
  if (await hasCollectionData(name)) return 0;
  for (const item of items) {
    await db.collection(name).add({ data: item });
  }
  return items.length;
}

async function ensureSeedData() {
  const seed = buildSeedData();
  const results = {};
  for (const key of Object.keys(seed)) {
    const collection = COLLECTIONS[key];
    if (!collection) continue;
    results[key] = await seedCollection(collection, seed[key]);
  }
  return results;
}

async function getCollectionList(collection, orderField = 'createdAt', order = 'desc') {
  try {
    const res = await db.collection(collection).orderBy(orderField, order).get();
    return res.data || [];
  } catch (error) {
    const res = await db.collection(collection).get();
    return res.data || [];
  }
}

async function findOneById(collection, id) {
  if (!id) return null;
  try {
    const byDocId = await db.collection(collection).doc(id).get();
    if (byDocId.data) return byDocId.data;
  } catch (error) {}
  const res = await db.collection(collection).where({ id }).limit(1).get();
  return res.data[0] || null;
}

async function getUserById(id) {
  return findOneById(COLLECTIONS.users, id);
}

async function getAgreement() {
  const res = await db.collection(COLLECTIONS.agreements).where({ isActive: true }).limit(1).get();
  return res.data[0] || invokeMockService('getAgreementContent');
}

async function getSchools() {
  const list = await getCollectionList(COLLECTIONS.schools, 'createdAt', 'asc');
  return list.length ? list : invokeMockService('getSchoolList').list;
}

async function validateSchoolCollege(schoolName, collegeName) {
  const school = String(schoolName || '').trim();
  const college = String(collegeName || '').trim();
  const schools = await getSchools();
  const targetSchool = schools.find((item) => item.name === school);
  if (!targetSchool) {
    throw new Error('所选学校未在平台认证列表中，请联系管理员补充后再提交');
  }
  if (college && !(targetSchool.colleges || []).includes(college)) {
    throw new Error('所选学院与学校不匹配，请重新选择');
  }
  return { school, college };
}

async function getCategoriesFromDb() {
  const list = await getCollectionList(COLLECTIONS.categories, 'createdAt', 'asc');
  return list.length ? list.map((item) => item.name) : invokeMockService('getCategories').categories;
}

async function getCurrentUser(wxContext) {
  const openid = wxContext.OPENID;
  const existing = await db.collection(COLLECTIONS.users).where({ openid }).limit(1).get();
  if (existing.data.length) {
    const currentUser = existing.data[0];
    if (isLegacyAutoVerifiedUser(currentUser)) {
      const updatedAt = nowString();
      const repaired = {
        ...currentUser,
        ...buildUnverifiedUserData(currentUser),
        updatedAt
      };
      await db.collection(COLLECTIONS.users).doc(currentUser._id).update({
        data: {
          ...buildUnverifiedUserData(currentUser),
          updatedAt
        }
      });
      return repaired;
    }
    return currentUser;
  }

  const currentTime = nowString();
  const user = {
    id: `user-${Date.now()}`,
    openid,
    name: '未认证用户',
    role: '普通用户',
    avatarClass: 'a1',
    phone: '',
    email: '',
    instituteId: '',
    school: '',
    college: '',
    proofName: '',
    status: '未认证',
    isAdmin: false,
    createdAt: currentTime,
    updatedAt: currentTime
  };
  const addRes = await db.collection(COLLECTIONS.users).add({ data: user });
  return { ...user, _id: addRes._id };
}

async function getInstrumentsRaw() {
  const list = await getCollectionList(COLLECTIONS.instruments);
  return list;
}

async function getInstrumentById(id) {
  const fromDb = await findOneById(COLLECTIONS.instruments, id);
  if (fromDb) return fromDb;
  return null;
}

async function getInstrumentList(query = {}) {
  const { category = '全部', keyword = '' } = query;
  const source = await getInstrumentsRaw();
  return source.filter((item) => {
    const categoryMatched = category === '全部' || item.category === category;
    const keywordMatched =
      !keyword ||
      item.name.includes(keyword) ||
      String(item.school || '').includes(keyword) ||
      String(item.sellerName || '').includes(keyword) ||
      (item.disciplines || []).some((subject) => subject.includes(keyword)) ||
      (item.tags || []).some((tag) => tag.includes(keyword));
    return categoryMatched && keywordMatched;
  });
}

function buildCartItem(record, instrument) {
  if (!record || !instrument) return null;
  const tradeMode = normalizeTradeMode(instrument, record.tradeMode);
  const insurancePlan = getInsurancePlanById(instrument, record.insurancePlanId);
  const quantity = record.quantity || 1;
  const insuranceAccepted = !!record.insuranceAccepted;
  let startDate = '';
  let endDate = '';
  let rentDays = 0;
  let rentalAmount = 0;
  let saleAmount = 0;
  let deposit = 0;
  let insuranceFee = 0;
  let amountLabel = instrument.priceLabel;
  let dateLabel = '一次性交付';

  if (tradeMode === '出售') {
    saleAmount = instrument.salePrice || 0;
    insuranceFee = insuranceAccepted && insurancePlan ? insurancePlan.fee * quantity : 0;
    amountLabel = instrument.salePriceLabel || `¥${instrument.salePrice || 0} 买断`;
  } else {
    const selection = normalizeDateSelection(instrument, record.startDate, record.endDate);
    startDate = selection.startDate;
    endDate = selection.endDate;
    rentDays = dayDiff(startDate, endDate);
    rentalAmount = (instrument.price || 0) * rentDays * quantity;
    deposit = instrument.deposit || 0;
    insuranceFee = insuranceAccepted && insurancePlan ? insurancePlan.fee * rentDays * quantity : 0;
    amountLabel = instrument.priceLabel || asPriceLabel(instrument.price || 0);
    dateLabel = `${startDate} ~ ${endDate}`;
  }

  const total = rentalAmount + saleAmount + insuranceFee + deposit + (instrument.platformServiceFee || 0);
  return {
    ...record,
    instrument: clone(instrument),
    tradeMode,
    insurancePlan: clone(insurancePlan),
    insuranceAccepted,
    quantity,
    startDate,
    endDate,
    dateLabel,
    rentDays,
    rentalAmount,
    saleAmount,
    insuranceFee,
    deposit,
    platformServiceFee: instrument.platformServiceFee || 0,
    total,
    amountLabel
  };
}

function summarizeCart(list) {
  return {
    total: list.reduce((sum, item) => sum + item.total, 0),
    depositTotal: list.reduce((sum, item) => sum + item.deposit, 0),
    insuranceTotal: list.reduce((sum, item) => sum + item.insuranceFee, 0),
    rentalTotal: list.reduce((sum, item) => sum + item.rentalAmount, 0),
    saleTotal: list.reduce((sum, item) => sum + item.saleAmount, 0),
    serviceTotal: list.reduce((sum, item) => sum + item.platformServiceFee, 0),
    itemCount: list.length
  };
}

async function getUserCartRecords(userId) {
  const res = await db.collection(COLLECTIONS.cartItems).where({ userId }).get();
  return res.data || [];
}

async function getCartDetail(userId) {
  const records = await getUserCartRecords(userId);
  const list = [];
  for (const record of records) {
    const instrument = await getInstrumentById(record.instrumentId);
    const item = buildCartItem(record, instrument);
    if (item) list.push(item);
  }
  return { list: clone(list), ...summarizeCart(list) };
}

async function getFavorites(userId) {
  const res = await db.collection(COLLECTIONS.favorites).where({ userId }).get();
  return res.data || [];
}

async function buildProfile(user, wxContext) {
  const [certificationCount, instrumentCount, favoriteRecords, orderCount] = await Promise.all([
    db.collection(COLLECTIONS.certifications).where({ openid: wxContext.OPENID }).count(),
    db.collection(COLLECTIONS.instruments).where({ sellerId: user._id }).count(),
    getFavorites(user._id),
    db.collection(COLLECTIONS.orders).where({ buyerUserId: user._id }).count()
  ]);
  return {
    certification: {
      status: user.status,
      name: user.name,
      role: user.role,
      phone: user.phone,
      email: user.email,
      instituteId: user.instituteId,
      school: user.school,
      college: user.college,
      proofName: user.proofName,
      isAdmin: isAdminUser(user),
      pendingMessage: getCertificationPendingMessage(user.status)
    },
    orderCount: orderCount.total,
    favoriteCount: favoriteRecords.length,
    instrumentCount: instrumentCount.total,
    certificationCount: certificationCount.total
  };
}

async function createCertification(payload, wxContext) {
  const form = {
    name: String(payload.name || '').trim(),
    phone: String(payload.phone || '').trim(),
    email: String(payload.email || '').trim(),
    instituteId: String(payload.instituteId || '').trim(),
    proofName: String(payload.proofName || '').trim(),
    role: String(payload.role || '科研工作者').trim(),
    school: String(payload.school || '').trim(),
    college: String(payload.college || '').trim()
  };
  if (!form.name || !form.phone || !form.email || !form.instituteId || !form.proofName) {
    throw new Error('请完整填写认证信息');
  }
  if (!validatePhone(form.phone)) throw new Error('手机号格式不正确');
  if (!validateEmail(form.email)) throw new Error('邮箱格式不正确');
  await validateSchoolCollege(form.school, form.college);

  const user = await getCurrentUser(wxContext);
  const submittedAt = nowString();
  const application = {
    id: `cert-${Date.now()}`,
    ...form,
    openid: wxContext.OPENID,
    userId: user._id,
    status: '待审核',
    submittedAt,
    createdAt: submittedAt
  };
  const pending = await db
    .collection(COLLECTIONS.certifications)
    .where({ userId: user._id, status: '待审核' })
    .limit(1)
    .get();
  if (pending.data.length) {
    await db.collection(COLLECTIONS.certifications).doc(pending.data[0]._id).update({
      data: {
        ...form,
        submittedAt,
        updatedAt: submittedAt
      }
    });
  } else {
    await db.collection(COLLECTIONS.certifications).add({ data: application });
  }
  await db.collection(COLLECTIONS.users).doc(user._id).update({
    data: { ...form, status: '待审核', updatedAt: submittedAt }
  });
  return {
    success: true,
    status: '待审核',
    message: pending.data.length
      ? '待审核认证申请已更新，平台会按最新资料继续审核。'
      : '认证信息已提交，已进入学校 / 机构审核流程。'
  };
}

async function resetCurrentUserCertification(wxContext) {
  const user = await getCurrentUser(wxContext);
  const updatedAt = nowString();
  await db.collection(COLLECTIONS.users).doc(user._id).update({
    data: {
      ...buildUnverifiedUserData(user),
      updatedAt
    }
  });

  const pending = await db.collection(COLLECTIONS.certifications).where({ userId: user._id, status: '待审核' }).get();
  for (const item of pending.data || []) {
    await db.collection(COLLECTIONS.certifications).doc(item._id).update({
      data: { status: '已撤回', reviewedAt: updatedAt }
    });
  }

  return {
    success: true,
    status: '未认证',
    message: '当前账号已重置为未认证状态，请重新填写并提交认证信息。'
  };
}

async function adminLogin(payload, wxContext) {
  const username = String(payload.username || '').trim();
  const password = String(payload.password || '').trim();
  const passwordHash = crypto.createHash('sha256').update(password).digest('hex');
  if (username !== ADMIN_LOGIN_USERNAME || passwordHash !== ADMIN_LOGIN_PASSWORD_HASH) {
    throw new Error('管理员账号或密码错误');
  }
  const user = await getCurrentUser(wxContext);
  await db.collection(COLLECTIONS.users).doc(user._id).update({
    data: {
      isAdmin: true,
      updatedAt: nowString()
    }
  });
  return { success: true, message: '管理员登录成功' };
}

async function adminLogout(wxContext) {
  const user = await getCurrentUser(wxContext);
  await db.collection(COLLECTIONS.users).doc(user._id).update({
    data: {
      isAdmin: false,
      updatedAt: nowString()
    }
  });
  return { success: true, message: '已退出管理员模式' };
}

async function publishInstrument(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  ensureVerified(user, '发布仪器');

  const tradeModes = normalizeTradeModes(payload.tradeModes, ['租赁']);
  const defaultTradeMode = tradeModes.includes(payload.defaultTradeMode) ? payload.defaultTradeMode : tradeModes[0];
  const price = Number(payload.price || 0);
  const salePrice = Number(payload.salePrice || 0);
  const deposit = tradeModes.includes('租赁') ? Number(payload.deposit || 0) : 0;
  const name = String(payload.name || '').trim();
  const category = String(payload.category || '').trim();
  const location = String(payload.location || '').trim();
  const desc = String(payload.desc || '').trim();
  if (!name || !category || !location || !desc) {
    throw new Error('请完整填写仪器基础信息');
  }
  if (!Number.isFinite(price) || price < 0) throw new Error('租赁日价格式不正确');
  if (!Number.isFinite(salePrice) || salePrice < 0) throw new Error('买断价格格式不正确');
  if (!Number.isFinite(deposit) || deposit < 0) throw new Error('押金格式不正确');
  if (tradeModes.includes('租赁') && !price) throw new Error('启用租赁模式时，请填写日租价');
  if (tradeModes.includes('出售') && !salePrice) throw new Error('启用出售模式时，请填写买断价');

  const template = invokeMockService('getInstrumentDetail', { id: 'ins-001' }).instrument;
  const disciplines = String(payload.disciplines || '')
    .split(/[\u3001\uff0c,/\n]+/)
    .map((item) => item.trim())
    .filter(Boolean);
  const breachRules = String(payload.breachRulesText || '')
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean);
  const damageRules = String(payload.damageRulesText || '')
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean);
  const images = Array.isArray(payload.images)
    ? payload.images.map((item) => String(item || '').trim()).filter(Boolean).slice(0, 5)
    : [];
  const agreement = await getAgreement();
  const currentTime = nowString();

  const instrument = {
    id: `ins-${Date.now()}`,
    name,
    category,
    sellerId: user._id,
    sellerName: user.name,
    sellerRole: user.role,
    institute: `${user.school} / ${user.college}`,
    school: user.school,
    college: user.college,
    verifiedType: 'blue',
    avatarClass: user.avatarClass || 'a4',
    posterTheme: payload.posterTheme || 'poster-theme-4',
    images,
    coverImage: String(payload.coverImage || images[0] || '').trim(),
    location,
    phone: user.phone,
    email: user.email,
    price,
    priceLabel: price ? asPriceLabel(price) : '仅支持出售',
    salePrice,
    salePriceLabel: salePrice ? `¥${salePrice} 买断` : '仅支持租赁',
    tradeModes,
    defaultTradeMode,
    deposit,
    platformServiceFee: 20,
    desc,
    precision: String(payload.precision || '参数待补充').trim(),
    disciplines: disciplines.length ? disciplines : ['综合研究'],
    withDataPackage: !!payload.withDataPackage,
    remote: !!payload.remote,
    supportInsurance: true,
    availableDates: payload.availableDates || template.availableDates,
    tags: ['已认证', payload.remote ? '远程实验' : '线下交接', tradeModes.length === 2 ? '租售皆可' : tradeModes[0]],
    condition: payload.condition || '新发布',
    publishStatus: '已上架',
    breachRules: breachRules.length ? breachRules : ['超时归还按平台合同规则处理'],
    damageRules: damageRules.length ? damageRules : ['人为损坏按检修报价赔付'],
    insurancePlans: clone(template.insurancePlans),
    agreementId: agreement.id || agreement._id,
    servicePackage: String(
      payload.servicePackage || (payload.withDataPackage ? '附带数据处理说明' : '仅提供仪器使用')
    ).trim(),
    createdAt: currentTime,
    updatedAt: currentTime
  };
  await db.collection(COLLECTIONS.instruments).add({ data: instrument });
  return { success: true, instrumentId: instrument.id, message: '仪器发布成功。' };
}

async function updateInstrument(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  ensureVerified(user, '编辑仪器');
  const instrument = await getInstrumentById(payload.id);
  if (!instrument) throw new Error('仪器不存在');
  if (instrument.sellerId !== user._id) throw new Error('只能编辑自己发布的仪器');

  const tradeModes = normalizeTradeModes(payload.tradeModes, instrument.tradeModes || ['租赁']);
  const defaultTradeMode = tradeModes.includes(payload.defaultTradeMode) ? payload.defaultTradeMode : tradeModes[0];
  const price = Number(payload.price || 0);
  const salePrice = Number(payload.salePrice || 0);
  const deposit = tradeModes.includes('租赁') ? Number(payload.deposit || 0) : 0;
  if (!Number.isFinite(price) || price < 0) throw new Error('租赁日价格式不正确');
  if (!Number.isFinite(salePrice) || salePrice < 0) throw new Error('买断价格格式不正确');
  if (!Number.isFinite(deposit) || deposit < 0) throw new Error('押金格式不正确');
  if (tradeModes.includes('租赁') && !price) throw new Error('启用租赁模式时，请填写日租价');
  if (tradeModes.includes('出售') && !salePrice) throw new Error('启用出售模式时，请填写买断价');
  const images = Array.isArray(payload.images)
    ? payload.images.map((item) => String(item || '').trim()).filter(Boolean).slice(0, 5)
    : Array.isArray(instrument.images)
      ? instrument.images
      : [];

  await db.collection(COLLECTIONS.instruments).doc(instrument._id).update({
    data: {
      tradeModes,
      defaultTradeMode,
      price,
      priceLabel: price ? asPriceLabel(price) : '仅支持出售',
      salePrice,
      salePriceLabel: salePrice ? `¥${salePrice} 买断` : '仅支持租赁',
      deposit,
      location: String(payload.location || '').trim(),
      desc: String(payload.desc || '').trim(),
      precision: String(payload.precision || instrument.precision || '').trim(),
      disciplines: String(payload.disciplines || '')
        .split(/[\u3001\uff0c,/\n]+/)
        .map((item) => item.trim())
        .filter(Boolean),
      remote: !!payload.remote,
      withDataPackage: !!payload.withDataPackage,
      servicePackage: String(payload.servicePackage || instrument.servicePackage || '').trim(),
      images,
      coverImage: String(payload.coverImage || images[0] || instrument.coverImage || '').trim(),
      breachRules: String(payload.breachRulesText || '')
        .split(/\n+/)
        .map((item) => item.trim())
        .filter(Boolean),
      damageRules: String(payload.damageRulesText || '')
        .split(/\n+/)
        .map((item) => item.trim())
        .filter(Boolean),
      updatedAt: nowString()
    }
  });
  return { success: true, message: '仪器信息已更新' };
}

async function toggleFavorite(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  const instrument = await getInstrumentById(payload.instrumentId);
  if (!instrument) throw new Error('未找到仪器');

  const existing = await db
    .collection(COLLECTIONS.favorites)
    .where({ userId: user._id, instrumentId: payload.instrumentId })
    .limit(1)
    .get();
  if (existing.data.length) {
    await db.collection(COLLECTIONS.favorites).doc(existing.data[0]._id).remove();
    return { success: true, isFavorite: false, message: '已取消收藏' };
  }
  await db.collection(COLLECTIONS.favorites).add({
    data: { id: `fav-${Date.now()}`, userId: user._id, instrumentId: payload.instrumentId, createdAt: nowString() }
  });
  return { success: true, isFavorite: true, message: '已加入收藏' };
}

async function getFavoriteList(wxContext) {
  const user = await getCurrentUser(wxContext);
  const favorites = await getFavorites(user._id);
  const list = [];
  for (const favorite of favorites) {
    const instrument = await getInstrumentById(favorite.instrumentId);
    if (instrument) list.push(instrument);
  }
  return { list: clone(list) };
}

async function addToCart(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  ensureVerified(user, '加入购物车');
  const instrument = await getInstrumentById(payload.instrumentId);
  if (!instrument) throw new Error('未找到仪器');
  ensureNotOwnInstrument(instrument, user, '加入购物车');

  const tradeMode = normalizeTradeMode(instrument, payload.tradeMode);
  const selection = normalizeDateSelection(instrument, payload.startDate, payload.endDate);
  const insurancePlanId = payload.insurancePlanId || (instrument.insurancePlans[0] && instrument.insurancePlans[0].id);
  const existing = await db
    .collection(COLLECTIONS.cartItems)
    .where({ userId: user._id, instrumentId: instrument.id, tradeMode })
    .limit(1)
    .get();

  const data = {
    startDate: selection.startDate,
    endDate: selection.endDate,
    insurancePlanId,
    insuranceAccepted: !!payload.insuranceAccepted,
    updatedAt: nowString()
  };

  if (existing.data.length) {
    await db.collection(COLLECTIONS.cartItems).doc(existing.data[0]._id).update({ data });
  } else {
    await db.collection(COLLECTIONS.cartItems).add({
      data: {
        id: `cart-${Date.now()}`,
        userId: user._id,
        instrumentId: instrument.id,
        tradeMode,
        quantity: 1,
        createdAt: nowString(),
        ...data
      }
    });
  }
  const count = await db.collection(COLLECTIONS.cartItems).where({ userId: user._id }).count();
  return { success: true, message: '已加入购物车', cartCount: count.total };
}

async function removeCartItem(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  const record = await findOneById(COLLECTIONS.cartItems, payload.id);
  if (!record || record.userId !== user._id) throw new Error('购物车记录不存在');
  await db.collection(COLLECTIONS.cartItems).doc(record._id).remove();
  return { success: true };
}

async function getOrderPreview(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  let detail = await getCartDetail(user._id);
  let first = detail.list[0];

  if (payload.instrumentId) {
    const instrument = await getInstrumentById(payload.instrumentId);
    if (!instrument) throw new Error('未找到仪器');
    const previewItem = buildCartItem(
      {
        id: `preview-${instrument.id}`,
        userId: user._id,
        instrumentId: instrument.id,
        tradeMode: payload.tradeMode,
        startDate: payload.startDate,
        endDate: payload.endDate,
        insurancePlanId: payload.insurancePlanId,
        insuranceAccepted: !!payload.insuranceAccepted,
        quantity: 1
      },
      instrument
    );
    const list = previewItem ? [previewItem] : [];
    detail = { list: clone(list), ...summarizeCart(list) };
    first = previewItem;
  }

  return {
    ...detail,
    contactName: user.name,
    contactPhone: user.phone,
    contactEmail: user.email,
    agreement: clone(await getAgreement()),
    defaultAgreementAccepted: false,
    defaultInsuranceAccepted: first ? !!first.insuranceAccepted : false,
    defaultDamageAccepted: false,
    selectedInstrument: first ? clone(first.instrument) : null,
    selectedItem: first ? clone(first) : null
  };
}

async function findChatByBuyerAndInstrument(userId, instrumentId) {
  const existing = await db
    .collection(COLLECTIONS.chats)
    .where({ buyerUserId: userId, instrumentId })
    .limit(1)
    .get();
  return existing.data[0] || null;
}

async function findChatForOrder(order) {
  if (!order) return null;
  const byOrder = await findChatByOrderId(order.id);
  if (byOrder) return byOrder;
  if (!order.instrumentId || !order.buyerUserId || !order.sellerId) return null;
  const reusable = await findChatByParticipants(order.buyerUserId, order.sellerId, order.instrumentId);
  return reusable && (!reusable.orderId || reusable.orderId === order.id) ? reusable : null;
}

function canAccessOrder(order, user) {
  return !!(order && user && (order.buyerUserId === user._id || order.sellerId === user._id || isAdminUser(user)));
}

function canManagePayment(order, user) {
  return !!(order && user && (order.buyerUserId === user._id || isAdminUser(user)));
}

function canAccessChat(chat, user) {
  return !!(chat && user && (chat.buyerUserId === user._id || chat.sellerId === user._id || isAdminUser(user)));
}

async function getChatCounterparty(chat, user) {
  if (chat && user && chat.sellerId === user._id && chat.buyerUserId !== user._id) {
    const buyer = chat.buyerUserId ? await getUserById(chat.buyerUserId) : null;
    return {
      name: chat.buyerName || (buyer && buyer.name) || '买方用户',
      role: chat.buyerRole || (buyer && buyer.role) || '买方'
    };
  }
  return {
    name: chat && chat.sellerName ? chat.sellerName : '发布方',
    role: chat && chat.sellerRole ? chat.sellerRole : '仪器发布方'
  };
}

async function findChatByParticipants(buyerUserId, sellerId, instrumentId) {
  const existing = await db
    .collection(COLLECTIONS.chats)
    .where({ buyerUserId, sellerId, instrumentId })
    .limit(1)
    .get();
  return existing.data[0] || null;
}

async function findChatByOrderId(orderId) {
  if (!orderId) return null;
  const existing = await db.collection(COLLECTIONS.chats).where({ orderId }).limit(1).get();
  return existing.data[0] || null;
}

function isChatParticipant(chat, user) {
  if (!chat || !user) return false;
  return chat.buyerUserId === user._id || chat.sellerId === user._id || isAdminUser(user);
}

function buildChatCounterpart(chat, user) {
  if (chat && user && chat.sellerId === user._id) {
    return {
      counterpartName: chat.buyerName || '研究需求方',
      counterpartRole: chat.buyerRole || '研究用户'
    };
  }
  return {
    counterpartName: chat ? chat.sellerName : '',
    counterpartRole: chat ? chat.sellerRole : ''
  };
}

async function ensureChatForOrder(order, instrument) {
  const timestamp = nowString();
  const displayTime = timestamp.slice(11, 16);
  const existingForOrder = await findChatByOrderId(order.id);
  if (existingForOrder) {
    await db.collection(COLLECTIONS.chats).doc(existingForOrder._id).update({
      data: { updatedAt: displayTime }
    });
    return existingForOrder;
  }

  const reusable = await findChatByParticipants(order.buyerUserId, order.sellerId, instrument.id);
  if (reusable && !reusable.orderId) {
    await db.collection(COLLECTIONS.chats).doc(reusable._id).update({
      data: { orderId: order.id, updatedAt: displayTime }
    });
    await db.collection(COLLECTIONS.chatMessages).add({
      data: {
        id: `msg-${Date.now()}`,
        chatId: reusable.id,
        from: "system",
        text: `?? ${order.id} ???????????????????????`,
        time: displayTime,
        createdAt: timestamp
      }
    });
    return { ...reusable, orderId: order.id, updatedAt: displayTime };
  }

  const buyer = (order.buyerUserId && (await getUserById(order.buyerUserId))) || null;
  const chat = {
    id: `chat-${Date.now()}`,
    orderId: order.id,
    instrumentId: instrument.id,
    buyerUserId: order.buyerUserId,
    buyerName: order.buyerName || (buyer && buyer.name) || "????",
    buyerRole: order.buyerRole || (buyer && buyer.role) || "????",
    sellerId: instrument.sellerId,
    sellerName: instrument.sellerName,
    sellerRole: instrument.sellerRole,
    instrumentName: instrument.name,
    supportIntervened: false,
    updatedAt: displayTime,
    createdAt: timestamp
  };
  await db.collection(COLLECTIONS.chats).add({ data: chat });
  await db.collection(COLLECTIONS.chatMessages).add({
    data: {
      id: `msg-${Date.now()}`,
      chatId: chat.id,
      from: "system",
      text: `?? ${order.id} ????????????????????`,
      time: displayTime,
      createdAt: timestamp
    }
  });
  return chat;
}

async function ensureOrderChat(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  const order = await getOrderById(payload.orderId);
  await ensureOrderAccess(order, user, "??????");
  if (!order || !order.instrumentId || !order.sellerId) {
    throw new Error("??????????????");
  }
  const instrument = await getInstrumentById(order.instrumentId);
  if (!instrument) throw new Error("????????????");
  const chat = await ensureChatForOrder(order, instrument);
  return { chatId: chat.id };
}

async function ensureInstrumentChat(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  ensureVerified(user, '联系发布方');
  const instrument = await getInstrumentById(payload.instrumentId);
  if (!instrument) throw new Error('未找到仪器');
  ensureNotOwnInstrument(instrument, user, '联系发布方');

  const existing = await findChatByBuyerAndInstrument(user._id, instrument.id);
  if (existing) {
    await db.collection(COLLECTIONS.chats).doc(existing._id).update({
      data: { updatedAt: nowString().slice(11, 16) }
    });
    return { chatId: existing.id };
  }

  const chat = {
    id: `chat-${Date.now()}`,
    instrumentId: instrument.id,
    buyerUserId: user._id,
    buyerName: user.name,
    buyerRole: user.role,
    sellerId: instrument.sellerId,
    sellerName: instrument.sellerName,
    sellerRole: instrument.sellerRole,
    instrumentName: instrument.name,
    supportIntervened: false,
    updatedAt: nowString().slice(11, 16),
    createdAt: nowString()
  };
  await db.collection(COLLECTIONS.chats).add({ data: chat });
  await db.collection(COLLECTIONS.chatMessages).add({
    data: {
      id: `msg-${Date.now()}`,
      chatId: chat.id,
      from: 'system',
      text: `已为你创建与 ${instrument.sellerName} 的咨询会话，可先沟通参数、排期和交付方式。`,
      time: nowString().slice(11, 16),
      createdAt: nowString()
    }
  });
  return { chatId: chat.id };
}

async function createConsultationOrder(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  ensureVerified(user, '远程实验咨询');
  const order = {
    id: `consult-${Date.now()}`,
    instrumentId: '',
    instrumentName: payload.topic || '远程实验咨询',
    buyerUserId: user._id,
    buyerName: user.name,
    buyerRole: user.role,
    sellerId: '',
    sellerName: '平台顾问',
    tradeMode: '远程实验咨询',
    topic: payload.topic,
    contact: payload.contact,
    requirement: payload.requirement || '',
    total: 0,
    amount: 0,
    status: '待平台联系',
    createdAt: nowString(),
    agreementTitle: '远程实验咨询服务说明',
    disputeEligible: false,
    deliveryType: '平台顾问对接'
  };
  await db.collection(COLLECTIONS.orders).add({ data: order });
  return { success: true, orderId: order.id, orderNo: order.id, message: '平台顾问会尽快联系你。' };
}

async function createOrder(payload, wxContext) {
  if (payload.mode === '远程实验咨询' && !payload.instrumentId) {
    return createConsultationOrder(payload, wxContext);
  }

  const user = await getCurrentUser(wxContext);
  ensureVerified(user, '下单');
  if (!payload.agreementAccepted || !payload.damageAccepted) {
    throw new Error('请先同意协议与损坏责任说明');
  }

  const cartDetail = await getCartDetail(user._id);
  const instrument =
    (payload.instrumentId && (await getInstrumentById(payload.instrumentId))) ||
    (cartDetail.list[0] && cartDetail.list[0].instrument);
  if (!instrument) throw new Error('未找到仪器');
  ensureNotOwnInstrument(instrument, user, '下单');

  const tradeMode = normalizeTradeMode(instrument, payload.tradeMode);
  const insurancePlan = getInsurancePlanById(instrument, payload.insurancePlanId);
  const insuranceAccepted = !!payload.insuranceAccepted;
  let startDate = '';
  let endDate = '';
  let rentDays = 0;
  let rentalAmount = 0;
  let saleAmount = 0;
  let deposit = 0;

  if (tradeMode === '租赁') {
    if (!payload.startDate || !payload.endDate) throw new Error('请选择租赁日期');
    const selection = normalizeDateSelection(instrument, payload.startDate, payload.endDate);
    startDate = selection.startDate;
    endDate = selection.endDate;
    rentDays = dayDiff(startDate, endDate);
    rentalAmount = instrument.price * rentDays;
    deposit = instrument.deposit;
  } else {
    saleAmount = instrument.salePrice || 0;
    if (!saleAmount) throw new Error('该仪器暂不支持买断');
  }

  const insuranceFee = insuranceAccepted && insurancePlan ? insurancePlan.fee * (tradeMode === '租赁' ? rentDays : 1) : 0;
  const total = rentalAmount + saleAmount + insuranceFee + deposit + instrument.platformServiceFee;
  const order = {
    id: `ord-${Date.now()}`,
    instrumentId: instrument.id,
    buyerUserId: user._id,
    buyerName: user.name,
    sellerId: instrument.sellerId,
    sellerName: instrument.sellerName,
    tradeMode,
    startDate,
    endDate,
    rentDays,
    dailyPrice: instrument.price,
    salePrice: instrument.salePrice || 0,
    rentalAmount,
    saleAmount,
    insurancePlan: clone(insurancePlan),
    insuranceAccepted,
    insuranceFee,
    deposit,
    platformServiceFee: instrument.platformServiceFee,
    total,
    amount: total,
    remark: payload.remark || '',
    agreementAccepted: true,
    damageAccepted: true,
    status: '待付款',
    createdAt: nowString(),
    agreementTitle: (await getAgreement()).title,
    disputeEligible: true,
    deliveryType: tradeMode === '出售' ? '平台验货与物流交付' : instrument.remote ? '远程实验排期' : '线下交接'
  };
  await db.collection(COLLECTIONS.orders).add({ data: order });

  const cartRecords = await db
    .collection(COLLECTIONS.cartItems)
    .where({ userId: user._id, instrumentId: instrument.id, tradeMode })
    .get();
  for (const item of cartRecords.data || []) {
    await db.collection(COLLECTIONS.cartItems).doc(item._id).remove();
  }
  await ensureChatForOrder(order, instrument);
  return { success: true, orderId: order.id, orderNo: order.id, amount: order.total, message: '订单已创建' };
}

async function getOrderById(id) {
  return findOneById(COLLECTIONS.orders, id);
}

async function ensureOrderAccess(order, user, actionName) {
  if (!order) throw new Error("?????");
  if (order.buyerUserId !== user._id && order.sellerId !== user._id && !isAdminUser(user)) {
    throw new Error(`${actionName || "????"}???????`);
  }
}

async function ensurePaymentAccess(order, user, actionName) {
  if (!order) throw new Error("?????");
  if (!canManagePayment(order, user)) {
    throw new Error(`${actionName || "????"}?????????`);
  }
}

async function getOrderList(wxContext) {
  const user = await getCurrentUser(wxContext);
  const buyerRes = await db.collection(COLLECTIONS.orders).where({ buyerUserId: user._id }).get();
  const sellerRes = await db.collection(COLLECTIONS.orders).where({ sellerId: user._id }).get();
  const orderMap = new Map();
  [...(buyerRes.data || []), ...(sellerRes.data || [])].forEach((item) => {
    if (!orderMap.has(item.id)) {
      orderMap.set(item.id, item);
    }
  });
  const list = [];
  for (const item of orderMap.values()) {
    const instrument = item.instrumentId ? await getInstrumentById(item.instrumentId) : null;
    list.push({
      ...item,
      instrument: instrument
        ? clone(instrument)
        : { name: item.instrumentName || item.topic || '远程实验咨询需求' }
    });
  }
  list.sort((a, b) => String(b.createdAt || '').localeCompare(String(a.createdAt || '')));
  return { list: clone(list) };
}

async function getOrderDetail(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  const order = await getOrderById(payload.id || payload.orderId);
  await ensureOrderAccess(order, user, "????");
  const instrument = order.instrumentId ? await getInstrumentById(order.instrumentId) : null;
  const chat = await findChatForOrder(order);
  return {
    order: clone(order),
    instrument: instrument ? clone(instrument) : null,
    agreement: clone(await getAgreement()),
    chatId: chat ? chat.id : ""
  };
}

async function getPaymentInfo(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  const order = await getOrderById(payload.orderId);
  await ensurePaymentAccess(order, user, "??????");
  return { order: clone(order) };
}

async function confirmPayment(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  const order = await getOrderById(payload.orderId);
  await ensurePaymentAccess(order, user, "????");
  if (order.status !== "???") throw new Error("??????????");
  const status =
    order.tradeMode === "??"
      ? "??????"
      : order.tradeMode === "??????"
        ? "?????"
        : "??????";
  await db.collection(COLLECTIONS.orders).doc(order._id).update({
    data: { status, paidAt: nowString() }
  });
  return { success: true, orderId: order.id };
}

async function getChatList(wxContext) {
  const user = await getCurrentUser(wxContext);
  const buyerChats = await db.collection(COLLECTIONS.chats).where({ buyerUserId: user._id }).get();
  const sellerChats = await db.collection(COLLECTIONS.chats).where({ sellerId: user._id }).get();
  const chatMap = new Map();
  [...(buyerChats.data || []), ...(sellerChats.data || [])].forEach((item) => {
    if (!chatMap.has(item.id)) {
      chatMap.set(item.id, item);
    }
  });
  const list = [];
  for (const chat of chatMap.values()) {
    const messages = await db.collection(COLLECTIONS.chatMessages).where({ chatId: chat.id }).get();
    const rows = (messages.data || []).sort((a, b) => String(a.createdAt || "").localeCompare(String(b.createdAt || "")));
    const counterpart = buildChatCounterpart(chat, user);
    list.push({
      id: chat.id,
      orderId: chat.orderId || "",
      sellerName: counterpart.counterpartName,
      sellerRole: counterpart.counterpartRole,
      counterpartName: counterpart.counterpartName,
      counterpartRole: counterpart.counterpartRole,
      instrumentName: chat.instrumentName,
      lastMessage: rows.length ? rows[rows.length - 1].text : "????",
      updatedAt: chat.updatedAt,
      supportIntervened: !!chat.supportIntervened
    });
  }
  list.sort((a, b) => String(b.updatedAt || "").localeCompare(String(a.updatedAt || "")));
  return { list: clone(list) };
}

async function getChatDetail(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  const chat = await findOneById(COLLECTIONS.chats, payload.id);
  if (!chat || !isChatParticipant(chat, user)) {
    throw new Error("?????");
  }
  const messages = await db.collection(COLLECTIONS.chatMessages).where({ chatId: chat.id }).get();
  const rows = (messages.data || [])
    .sort((a, b) => String(a.createdAt || "").localeCompare(String(b.createdAt || "")))
    .map((item) => ({ from: item.from, text: item.text, time: item.time }));
  const counterpart = buildChatCounterpart(chat, user);
  return {
    chat: {
      id: chat.id,
      orderId: chat.orderId || "",
      instrumentId: chat.instrumentId,
      sellerName: counterpart.counterpartName,
      sellerRole: counterpart.counterpartRole,
      counterpartName: counterpart.counterpartName,
      counterpartRole: counterpart.counterpartRole,
      instrumentName: chat.instrumentName,
      supportIntervened: !!chat.supportIntervened
    },
    messages: clone(rows)
  };
}

async function sendChatMessage(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  const chat = await findOneById(COLLECTIONS.chats, payload.chatId);
  if (!chat || !isChatParticipant(chat, user)) throw new Error('会话不存在');
  const text = String(payload.text || '').trim();
  if (!text) throw new Error('请输入消息内容');
  const currentTime = nowString();
  const from = chat.sellerId === user._id ? 'seller' : 'buyer';
  await db.collection(COLLECTIONS.chatMessages).add({
    data: {
      id: `msg-${Date.now()}`,
      chatId: chat.id,
      from,
      text,
      time: currentTime.slice(11, 16),
      createdAt: currentTime
    }
  });
  await db.collection(COLLECTIONS.chats).doc(chat._id).update({
    data: { updatedAt: currentTime.slice(11, 16) }
  });
  return getChatDetail({ id: chat.id }, wxContext);
}

async function requestSupportIntervention(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  const chat = await findOneById(COLLECTIONS.chats, payload.chatId);
  if (!chat || !isChatParticipant(chat, user)) throw new Error('会话不存在');
  const currentTime = nowString();
  await db.collection(COLLECTIONS.chats).doc(chat._id).update({
    data: { supportIntervened: true, updatedAt: currentTime.slice(11, 16) }
  });
  await db.collection(COLLECTIONS.chatMessages).add({
    data: {
      id: `msg-${Date.now()}`,
      chatId: chat.id,
      from: 'system',
      text: '平台客服已介入，将结合聊天记录与订单信息帮助协调。',
      time: currentTime.slice(11, 16),
      createdAt: currentTime
    }
  });
  return { success: true, message: '平台客服已介入' };
}

async function getRatingList(wxContext) {
  const user = await getCurrentUser(wxContext);
  const res = await db.collection(COLLECTIONS.ratings).where({ userId: user._id }).get();
  return { list: clone(res.data || []) };
}

async function publishRating(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  const order = await getOrderById(payload.orderId);
  await ensureOrderAccess(order, user, '评价订单');
  if (!['已完成', '平台已结案'].includes(order.status)) {
    throw new Error('订单未完成，暂不可评价');
  }
  const existing = await db
    .collection(COLLECTIONS.ratings)
    .where({ userId: user._id, orderId: payload.orderId })
    .limit(1)
    .get();
  if (existing.data.length) throw new Error('该订单已评价');
  await db.collection(COLLECTIONS.ratings).add({
    data: {
      id: `rate-${Date.now()}`,
      userId: user._id,
      orderId: payload.orderId,
      target: payload.target,
      score: Number(payload.score),
      content: payload.content,
      createdAt: nowString()
    }
  });
  return { success: true, message: '评价已提交' };
}

async function submitReport(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  if (!payload.targetName || !payload.reason) throw new Error('请填写举报原因');
  await db.collection(COLLECTIONS.reports).add({
    data: {
      id: `report-${Date.now()}`,
      targetType: payload.targetType,
      targetName: payload.targetName,
      reason: payload.reason,
      reporter: user.name,
      reporterUserId: user._id,
      status: '待处理',
      createdAt: nowString()
    }
  });
  return { success: true, message: '举报已提交' };
}

async function getReportList(wxContext) {
  const user = await getCurrentUser(wxContext);
  ensureAdmin(user, '查看举报');
  return { list: clone(await getCollectionList(COLLECTIONS.reports)) };
}

async function resolveReport(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  ensureAdmin(user, '处理举报');
  const report = await findOneById(COLLECTIONS.reports, payload.id);
  if (!report) throw new Error('举报不存在');
  await db.collection(COLLECTIONS.reports).doc(report._id).update({
    data: { status: '已处理', resolvedAt: nowString() }
  });
  return { success: true, message: '举报已处理' };
}

async function createDispute(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  if (!payload.orderId || !payload.summary) throw new Error('请填写争议原因');
  const order = await getOrderById(payload.orderId);
  await ensureOrderAccess(order, user, '提交争议');
  if (!order.disputeEligible) throw new Error('当前订单不支持发起争议');

  const existing = await db
    .collection(COLLECTIONS.disputes)
    .where({ orderId: payload.orderId })
    .limit(10)
    .get();
  if ((existing.data || []).some((item) => item.status !== '已结案')) {
    throw new Error('该订单已有处理中争议');
  }

  await db.collection(COLLECTIONS.disputes).add({
    data: {
      id: `dispute-${Date.now()}`,
      orderId: payload.orderId,
      buyerUserId: user._id,
      summary: payload.summary,
      status: '待平台受理',
      assignee: '平台客服 02',
      createdAt: nowString()
    }
  });
  await db.collection(COLLECTIONS.orders).doc(order._id).update({
    data: { status: '争议处理中' }
  });
  return { success: true, message: '争议已提交，平台客服将尽快介入' };
}

async function getDisputeList(wxContext) {
  const user = await getCurrentUser(wxContext);
  ensureAdmin(user, '查看纠纷');
  return { list: clone(await getCollectionList(COLLECTIONS.disputes)) };
}

async function resolveDispute(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  ensureAdmin(user, '处理纠纷');
  const dispute = await findOneById(COLLECTIONS.disputes, payload.id);
  if (!dispute) throw new Error('纠纷不存在');
  await db.collection(COLLECTIONS.disputes).doc(dispute._id).update({
    data: { status: '已结案', resolvedAt: nowString() }
  });
  const order = await getOrderById(dispute.orderId);
  if (order) {
    await db.collection(COLLECTIONS.orders).doc(order._id).update({
      data: { status: '平台已结案' }
    });
  }
  return { success: true, message: '纠纷已结案' };
}

async function getAdminDashboard(wxContext) {
  const user = await getCurrentUser(wxContext);
  ensureAdmin(user, '查看后台');
  const cmd = db.command;
  const [schoolsRes, instrumentsRes, certificationsRes, openDisputesRes, openReportsRes] = await Promise.all([
    db.collection(COLLECTIONS.schools).count(),
    db.collection(COLLECTIONS.instruments).count(),
    db.collection(COLLECTIONS.certifications).where({ status: '待审核' }).count(),
    db.collection(COLLECTIONS.disputes).where({ status: cmd.neq('已结案') }).count(),
    db.collection(COLLECTIONS.reports).where({ status: '待处理' }).count()
  ]);
  return {
    pendingCertification: certificationsRes.total,
    totalSchools: schoolsRes.total,
    totalInstruments: instrumentsRes.total,
    openDisputes: openDisputesRes.total,
    openReports: openReportsRes.total
  };
}

async function addSchool(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  ensureAdmin(user, '维护院校');
  const name = String(payload.name || '').trim();
  const colleges = Array.isArray(payload.colleges)
    ? payload.colleges.map((item) => String(item || '').trim()).filter(Boolean)
    : String(payload.colleges || '')
        .split(/[\n,，、/]+/)
        .map((item) => item.trim())
        .filter(Boolean);
  if (!name || !colleges.length) throw new Error('请填写学校与学院信息');

  const exists = await db.collection(COLLECTIONS.schools).where({ name }).limit(1).get();
  if (exists.data.length) {
    const current = exists.data[0];
    await db.collection(COLLECTIONS.schools).doc(current._id).update({
      data: { colleges: Array.from(new Set((current.colleges || []).concat(colleges))) }
    });
    return { success: true, message: '已合并进现有认证院校列表' };
  }
  await db.collection(COLLECTIONS.schools).add({
    data: { id: `sch-${Date.now()}`, name, colleges, createdAt: nowString() }
  });
  return { success: true, message: '学校 / 学院信息已添加到云数据库' };
}

async function getCertificationList(wxContext) {
  const user = await getCurrentUser(wxContext);
  ensureAdmin(user, '查看认证申请');
  return { list: clone(await getCollectionList(COLLECTIONS.certifications)) };
}

async function reviewCertification(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  ensureAdmin(user, '审核认证');
  const certification = await findOneById(COLLECTIONS.certifications, payload.id);
  if (!certification) throw new Error('申请不存在');
  const reviewedAt = nowString();
  await db.collection(COLLECTIONS.certifications).doc(certification._id).update({
    data: { status: payload.status, reviewedAt }
  });
  if (certification.userId) {
    const targetUser = await findOneById(COLLECTIONS.users, certification.userId);
    if (targetUser) {
      await db.collection(COLLECTIONS.users).doc(targetUser._id).update({
        data: { status: payload.status === '已通过' ? '已认证' : payload.status, updatedAt: reviewedAt }
      });
    }
  }
  return { success: true, message: '认证审核状态已更新' };
}

async function getCommunity() {
  const list = await getCollectionList(COLLECTIONS.posts);
  const tags = ['全部'].concat(Array.from(new Set(list.map((item) => item.tag).filter(Boolean))));
  return { tags, list: clone(list) };
}

async function getPostDetail(payload) {
  const post = await findOneById(COLLECTIONS.posts, payload.id);
  if (!post) throw new Error('帖子不存在');
  const list = await getCollectionList(COLLECTIONS.posts);
  return {
    post: clone(post),
    related: clone(list.filter((item) => item.id !== post.id && item.tag === post.tag).slice(0, 2))
  };
}

async function getProjects() {
  const list = await getCollectionList(COLLECTIONS.projects);
  const filters = ['全部'].concat(Array.from(new Set(list.map((item) => item.status).filter(Boolean))));
  return { filters, list: clone(list) };
}

async function getProjectDetail(payload) {
  const project = await findOneById(COLLECTIONS.projects, payload.id);
  if (!project) throw new Error('项目不存在');
  return { project: clone(project), flow: clone(project.flow || []), matrix: clone(project.matrix || []) };
}

async function publishProject(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  const title = String(payload.title || '').trim();
  const company = String(payload.company || '').trim();
  const needs = String(payload.needs || '').trim();
  if (!title || !company || !needs) throw new Error('请补充核心项目信息');
  const project = {
    id: `proj-${Date.now()}`,
    title,
    owner: user.name,
    company,
    domain: payload.domain || '综合研究',
    status: '招募中',
    intro: needs,
    budget: payload.budget || '预算待沟通',
    duration: payload.duration || '周期待沟通',
    keywords: [payload.domain || '综合研究', '平台发布', '科研合作'],
    targetRoles: ['高校教师', '科研工作者', '仪器供应方'],
    evaluation: {
      hard: '将结合仪器条件、团队经验和交付能力综合评估。',
      soft: '将结合沟通效率、协作记录和复盘质量综合评估。'
    },
    matches: [],
    flow: ['发布需求', '平台匹配', '双方沟通', '确认执行', '复盘验收'],
    matrix: [
      { label: '需求清晰度', value: '85%' },
      { label: '资源匹配度', value: '80%' },
      { label: '执行可行性', value: '82%' }
    ],
    needs,
    createdAt: nowString()
  };
  await db.collection(COLLECTIONS.projects).add({ data: project });
  return { success: true, projectId: project.id, message: '项目需求已发布，平台会进入匹配流程。' };
}

async function submitAiTask(payload, wxContext) {
  const user = await getCurrentUser(wxContext);
  const result = AI_TOOL_LIBRARY[payload.toolId] || AI_TOOL_LIBRARY['resource-match'];
  await db.collection(COLLECTIONS.aiTasks).add({
    data: {
      id: `ai-${Date.now()}`,
      userId: user._id,
      toolId: payload.toolId,
      goal: payload.goal,
      dataset: payload.dataset || '',
      result,
      createdAt: nowString()
    }
  });
  return clone(result);
}

async function invokeCloudService(action, payload, wxContext) {
  await ensureSeedData();

  switch (action) {
    case 'getHomeData': {
      const instruments = await getInstrumentList({ category: '全部', keyword: '' });
      const schools = await getSchools();
      const pending = await db.collection(COLLECTIONS.certifications).where({ status: '待审核' }).count();
      return {
        hero: {
          title: '神经突触仪器租赁与学术交流',
          subtitle: '以高校认证、科研背书和仪器风控为核心，把租赁、数据交付、远程实验和学术沟通做成一条真实链路。'
        },
        featuredInstruments: clone(instruments.slice(0, 6)),
        stats: [
          { label: '认证院校', value: `${schools.length} 所` },
          { label: '在架仪器', value: `${instruments.length} 台` },
          { label: '待审核认证', value: `${pending.total} 条` }
        ]
      };
    }
    case 'getCategories':
      return { categories: await getCategoriesFromDb(), schools: clone(await getSchools()) };
    case 'getInstruments':
      return { categories: await getCategoriesFromDb(), list: clone(await getInstrumentList(payload)) };
    case 'getInstrumentDetail': {
      const instrument = await getInstrumentById(payload.id);
      if (!instrument) throw new Error('未找到仪器');
      const user = await getCurrentUser(wxContext);
      const favorite = await db
        .collection(COLLECTIONS.favorites)
        .where({ userId: user._id, instrumentId: instrument.id })
        .limit(1)
        .get();
      const list = await getInstrumentList({ category: '全部', keyword: '' });
      return {
        instrument: clone(instrument),
        isFavorite: !!favorite.data.length,
        recommendations: clone(list.filter((item) => item.id !== instrument.id).slice(0, 2)),
        agreement: clone(await getAgreement())
      };
    }
    case 'toggleFavorite':
      return toggleFavorite(payload, wxContext);
    case 'getFavoriteList':
      return getFavoriteList(wxContext);
    case 'addToCart':
      return addToCart(payload, wxContext);
    case 'removeCartItem':
      return removeCartItem(payload, wxContext);
    case 'getCart': {
      const user = await getCurrentUser(wxContext);
      return getCartDetail(user._id);
    }
    case 'getOrderPreview':
      return getOrderPreview(payload, wxContext);
    case 'createOrder':
      return createOrder(payload, wxContext);
    case 'getPaymentInfo':
      return getPaymentInfo(payload, wxContext);
    case 'confirmPayment':
      return confirmPayment(payload, wxContext);
    case 'getOrderList':
      return getOrderList(wxContext);
    case 'getOrderDetail':
      return getOrderDetail(payload, wxContext);
    case 'getChatList':
      return getChatList(wxContext);
    case 'getChatDetail':
      return getChatDetail(payload, wxContext);
    case 'ensureInstrumentChat':
      return ensureInstrumentChat(payload, wxContext);
    case 'ensureOrderChat':
      return ensureOrderChat(payload, wxContext);
    case 'sendChatMessage':
      return sendChatMessage(payload, wxContext);
    case 'requestSupportIntervention':
      return requestSupportIntervention(payload, wxContext);
    case 'getProfile': {
      const user = await getCurrentUser(wxContext);
      return buildProfile(user, wxContext);
    }
    case 'adminLogin':
      return adminLogin(payload, wxContext);
    case 'adminLogout':
      return adminLogout(wxContext);
    case 'getSchoolOptions':
      return clone(await getSchools());
    case 'submitCertification':
      return createCertification(payload, wxContext);
    case 'resetCurrentUserCertification':
      return resetCurrentUserCertification(wxContext);
    case 'getMyInstruments': {
      const user = await getCurrentUser(wxContext);
      const res = await db.collection(COLLECTIONS.instruments).where({ sellerId: user._id }).get();
      return { list: clone(res.data || []) };
    }
    case 'publishInstrument':
      return publishInstrument(payload, wxContext);
    case 'getInstrumentEditDetail':
      return { instrument: clone(await getInstrumentById(payload.id)) };
    case 'updateInstrument':
      return updateInstrument(payload, wxContext);
    case 'createDispute':
      return createDispute(payload, wxContext);
    case 'getRatingList':
      return getRatingList(wxContext);
    case 'publishRating':
      return publishRating(payload, wxContext);
    case 'submitReport':
      return submitReport(payload, wxContext);
    case 'getAdminDashboard':
      return getAdminDashboard(wxContext);
    case 'getSchoolList':
      return { list: clone(await getSchools()) };
    case 'addSchool':
      return addSchool(payload, wxContext);
    case 'getCertificationList':
      return getCertificationList(wxContext);
    case 'reviewCertification':
      return reviewCertification(payload, wxContext);
    case 'getReportList':
      return getReportList(wxContext);
    case 'resolveReport':
      return resolveReport(payload, wxContext);
    case 'getDisputeList':
      return getDisputeList(wxContext);
    case 'resolveDispute':
      return resolveDispute(payload, wxContext);
    case 'getAgreementContent':
      return clone(await getAgreement());
    case 'getCommunity':
      return getCommunity();
    case 'getPostDetail':
      return getPostDetail(payload);
    case 'getProjects':
      return getProjects();
    case 'getProjectDetail':
      return getProjectDetail(payload);
    case 'publishProject':
      return publishProject(payload, wxContext);
    case 'submitAiTask':
      return submitAiTask(payload, wxContext);
    default:
      return invokeMockService(action, payload);
  }
}

module.exports = {
  ensureSeedData,
  invokeCloudService
};
