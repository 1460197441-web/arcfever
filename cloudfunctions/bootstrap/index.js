const cloud = require('wx-server-sdk');

cloud.init({
  env: cloud.DYNAMIC_CURRENT_ENV
});

exports.main = async () => {
  return {
    success: true,
    message: '当前项目默认可直接使用 mock 数据运行。如需持久化数据，可在此云函数内继续扩展数据库初始化逻辑。'
  };
};
