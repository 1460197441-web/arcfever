const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '登录失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    username: '',
    password: '',
    loading: false
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onInput(event) {
    this.setData({ [event.currentTarget.dataset.field]: event.detail.value });
  },
  submit() {
    const { username, password, loading } = this.data;
    if (loading) return;
    if (!username.trim() || !password.trim()) {
      wx.showToast({ title: '请输入账号和密码', icon: 'none' });
      return;
    }
    this.setData({ loading: true });
    callService('adminLogin', { username: username.trim(), password: password.trim() })
      .then((res) => {
        wx.showToast({ title: res.message, icon: 'none' });
        setTimeout(() => {
          wx.redirectTo({ url: '/pages/admin/index' });
        }, 300);
      })
      .catch(showError)
      .finally(() => {
        this.setData({ loading: false });
      });
  }
});
