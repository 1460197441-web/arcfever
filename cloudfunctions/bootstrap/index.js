const cloud = require('wx-server-sdk');
const { buildSeedData } = require('./seed-data');

cloud.init({
  env: cloud.DYNAMIC_CURRENT_ENV
});

const db = cloud.database();
const _ = db.command;

const COLLECTIONS = [
  'users',
  'schools',
  'instruments',
  'agreements',
  'certifications',
  'categories',
  'favorites',
  'cart_items',
  'orders',
  'chats',
  'chat_messages',
  'ratings',
  'reports',
  'disputes',
  'posts',
  'projects',
  'ai_tasks'
];

const DEMO_IDS = {
  users: ['seed-user-001'],
  certifications: ['cert-001', 'cert-002'],
  instruments: ['ins-001', 'ins-002', 'ins-003'],
  favorites: ['fav-001'],
  orders: ['ord-demo-001', 'ord-legacy-001'],
  chats: ['chat-001'],
  ratings: ['rate-001'],
  reports: ['report-001'],
  disputes: ['dispute-001']
};

async function ensureCollectionExists(name) {
  try {
    await db.collection(name).limit(1).get();
    return { name, created: false };
  } catch (error) {
    const msg = String(error && (error.errMsg || error.message || error));
    if (
      msg.includes('database collection not exists') ||
      msg.includes('Db or Table not exist') ||
      msg.includes('ResourceNotFound')
    ) {
      await db.createCollection(name);
      return { name, created: true };
    }
    throw error;
  }
}

async function seedCollection(name, items) {
  if (!items.length) return 0;

  const existing = await db.collection(name).limit(1).get();
  if (existing.data.length) return 0;

  for (const item of items) {
    await db.collection(name).add({ data: item });
  }

  return items.length;
}

async function removeByIds(collectionName, ids) {
  if (!ids || !ids.length) return 0;
  const matched = await db.collection(collectionName).where({ id: _.in(ids) }).get();
  let removed = 0;
  for (const item of matched.data || []) {
    await db.collection(collectionName).doc(item._id).remove();
    removed += 1;
  }
  return removed;
}

async function removeByQuery(collectionName, query) {
  const matched = await db.collection(collectionName).where(query).get();
  let removed = 0;
  for (const item of matched.data || []) {
    await db.collection(collectionName).doc(item._id).remove();
    removed += 1;
  }
  return removed;
}

async function purgeDemoData() {
  const results = {};
  results.chatMessages = await removeByQuery('chat_messages', { chatId: _.in(DEMO_IDS.chats) });
  results.favorites = await removeByIds('favorites', DEMO_IDS.favorites);
  results.ratings = await removeByIds('ratings', DEMO_IDS.ratings);
  results.reports = await removeByIds('reports', DEMO_IDS.reports);
  results.disputes = await removeByIds('disputes', DEMO_IDS.disputes);
  results.orders = await removeByIds('orders', DEMO_IDS.orders);
  results.chats = await removeByIds('chats', DEMO_IDS.chats);
  results.certifications = await removeByIds('certifications', DEMO_IDS.certifications);
  results.instruments = await removeByIds('instruments', DEMO_IDS.instruments);
  results.users = await removeByQuery('users', _.or([{ id: _.in(DEMO_IDS.users) }, { openid: 'mock-openid-001' }]));
  return results;
}

exports.main = async (event = {}) => {
  const mode = event.mode || 'purgeDemoData';

  if (mode === 'purgeDemoData') {
    const results = await purgeDemoData();
    return {
      success: true,
      message: 'demo data purged',
      results
    };
  }

  const seed = buildSeedData();
  const createdCollections = [];
  const results = {};

  for (const name of COLLECTIONS) {
    const result = await ensureCollectionExists(name);
    if (result.created) createdCollections.push(name);
  }

  results.users = await seedCollection('users', seed.users);
  results.schools = await seedCollection('schools', seed.schools);
  results.instruments = await seedCollection('instruments', seed.instruments);
  results.agreements = await seedCollection('agreements', seed.agreements);
  results.certifications = await seedCollection('certifications', seed.certifications);
  results.categories = await seedCollection('categories', seed.categories);
  results.favorites = await seedCollection('favorites', seed.favorites);
  results.cartItems = await seedCollection('cart_items', seed.cartItems);
  results.orders = await seedCollection('orders', seed.orders);
  results.chats = await seedCollection('chats', seed.chats);
  results.chatMessages = await seedCollection('chat_messages', seed.chatMessages);
  results.ratings = await seedCollection('ratings', seed.ratings);
  results.reports = await seedCollection('reports', seed.reports);
  results.disputes = await seedCollection('disputes', seed.disputes);
  results.posts = await seedCollection('posts', seed.posts);
  results.projects = await seedCollection('projects', seed.projects);
  results.aiTasks = await seedCollection('ai_tasks', seed.aiTasks);

  return {
    success: true,
    message: 'database initialized',
    createdCollections,
    results
  };
};
