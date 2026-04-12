const { callService } = require('../../utils/api');

const VERIFIED_STATUSES = ['已认证', '已通过'];

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '我的仪器加载失败',
    icon: 'none'
  });
}

Page({
  data: {
    loading: true,
    canManage: false,
    certificationStatus: '未认证',
    pendingMessage: '',
    list: []
  },
  onShow() {
    this.loadData();
  },
  loadData() {
    this.setData({ loading: true });
    callService('getProfile')
      .then((profile) => {
        const certification = (profile && profile.certification) || {};
        const canManage = VERIFIED_STATUSES.includes(certification.status);
        this.setData({
          canManage,
          certificationStatus: certification.status || '未认证',
          pendingMessage: certification.pendingMessage || ''
        });
        if (!canManage) {
          this.setData({ loading: false, list: [] });
          return null;
        }
        return callService('getMyInstruments');
      })
      .then((res) => {
        if (!res) return;
        this.setData({ list: res.list || [], loading: false });
      })
      .catch((error) => {
        this.setData({ loading: false });
        showError(error);
      });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  goPublish() {
    wx.switchTab({ url: '/pages/instrument-publish/index' });
  },
  goCertification() {
    wx.navigateTo({ url: '/pages/certification/index' });
  },
  goEdit(event) {
    wx.navigateTo({ url: `/pages/instrument-edit/index?id=${event.currentTarget.dataset.id}` });
  }
});
