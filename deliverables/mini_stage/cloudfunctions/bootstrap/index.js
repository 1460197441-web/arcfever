const cloud = require('wx-server-sdk');
const { buildSeedData } = require('./seed-data');

cloud.init({
  env: cloud.DYNAMIC_CURRENT_ENV
});

const db = cloud.database();

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

exports.main = async () => {
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
    message: '数据库初始化完成',
    createdCollections,
    results
  };
};
