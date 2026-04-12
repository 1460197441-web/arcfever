const { callService } = require('../../utils/api');

const VERIFIED_STATUSES = ['已认证', '已通过'];
const MAX_IMAGES = 5;

function createTradeModeOptions(selected = ['租赁']) {
  return ['租赁', '出售'].map((value) => ({
    value,
    selected: selected.includes(value)
  }));
}

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '提交失败，请稍后重试',
    icon: 'none'
  });
}

function chooseMediaAsync(count) {
  return new Promise((resolve, reject) => {
    wx.chooseMedia({
      count,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      sizeType: ['compressed'],
      success: resolve,
      fail: reject
    });
  });
}

Page({
  data: {
    loading: true,
    canPublish: false,
    certificationStatus: '未认证',
    pendingMessage: '',
    categories: [],
    categoryIndex: 0,
    tradeModeOptions: createTradeModeOptions(),
    uploadingImages: false,
    uploadHint: '最多上传 5 张图片，首页和详情页会优先展示第一张。',
    form: {
      name: '',
      price: '',
      salePrice: '',
      deposit: '',
      location: '',
      precision: '',
      disciplines: '',
      servicePackage: '',
      desc: '',
      breachRulesText: '',
      damageRulesText: '',
      withDataPackage: true,
      remote: false,
      images: []
    }
  },
  onLoad() {
    this.loadPageData();
  },
  onShow() {
    this.syncTabBar();
    this.loadPageData();
  },
  syncTabBar() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().syncSelected();
    }
  },
  loadPageData() {
    this.setData({ loading: true });
    Promise.all([callService('getCategories'), callService('getProfile')])
      .then(([res, profile]) => {
        const categories = (res.categories || []).filter((item) => item !== '全部');
        const certification = (profile && profile.certification) || {};
        const canPublish = VERIFIED_STATUSES.includes(certification.status);
        const nextCategoryIndex =
          categories.length && this.data.categoryIndex < categories.length ? this.data.categoryIndex : 0;

        this.setData({
          loading: false,
          categories,
          categoryIndex: nextCategoryIndex,
          canPublish,
          certificationStatus: certification.status || '未认证',
          pendingMessage: certification.pendingMessage || ''
        });
      })
      .catch((error) => {
        this.setData({ loading: false });
        showError(error);
      });
  },
  goCertification() {
    wx.navigateTo({ url: '/pages/certification/index' });
  },
  onInput(event) {
    this.setData({ [`form.${event.currentTarget.dataset.field}`]: event.detail.value });
  },
  onCategoryChange(event) {
    this.setData({ categoryIndex: Number(event.detail.value) });
  },
  toggleTradeMode(event) {
    const mode = event.currentTarget.dataset.mode;
    const selectedModes = this.data.tradeModeOptions
      .filter((item) => item.selected)
      .map((item) => item.value);

    let nextModes = selectedModes.includes(mode)
      ? selectedModes.filter((item) => item !== mode)
      : selectedModes.concat(mode);

    if (!nextModes.length) {
      nextModes = [mode];
    }

    this.setData({
      tradeModeOptions: createTradeModeOptions(nextModes)
    });
  },
  toggleFlag(event) {
    const field = event.currentTarget.dataset.field;
    this.setData({ [`form.${field}`]: !this.data.form[field] });
  },
  async chooseImages() {
    const remain = MAX_IMAGES - this.data.form.images.length;
    if (remain <= 0) {
      wx.showToast({ title: `最多上传 ${MAX_IMAGES} 张`, icon: 'none' });
      return;
    }

    try {
      const app = getApp();
      const res = await chooseMediaAsync(remain);
      const files = (res.tempFiles || []).map((item) => item.tempFilePath).filter(Boolean);
      if (!files.length) return;

      this.setData({ uploadingImages: true, uploadHint: '正在上传图片...' });

      let uploaded = [];
      if (app.globalData.useCloud && wx.cloud) {
        uploaded = await Promise.all(
          files.map((filePath, index) =>
            wx.cloud
              .uploadFile({
                cloudPath: `instrument-images/${Date.now()}-${index}-${Math.random()
                  .toString(16)
                  .slice(2)}.jpg`,
                filePath
              })
              .then((result) => result.fileID)
          )
        );
      } else {
        uploaded = files;
      }

      this.setData({
        'form.images': this.data.form.images.concat(uploaded).slice(0, MAX_IMAGES),
        uploadingImages: false,
        uploadHint:
          app.globalData.useCloud && wx.cloud
            ? '图片已上传，首页和详情页会展示第一张。'
            : '当前为本地演示模式，图片仅在本机预览。'
      });
    } catch (error) {
      this.setData({
        uploadingImages: false,
        uploadHint: '图片上传失败，请重试。'
      });
      showError(error);
    }
  },
  removeImage(event) {
    const index = Number(event.currentTarget.dataset.index);
    const nextImages = this.data.form.images.filter((_, itemIndex) => itemIndex !== index);
    this.setData({
      'form.images': nextImages,
      uploadHint: nextImages.length ? '已更新图片列表。' : '最多上传 5 张图片，首页和详情页会优先展示第一张。'
    });
  },
  previewImage(event) {
    const current = event.currentTarget.dataset.src;
    wx.previewImage({
      current,
      urls: this.data.form.images
    });
  },
  submit() {
    const { canPublish, form, categories, categoryIndex, tradeModeOptions } = this.data;
    if (!canPublish) {
      wx.showToast({ title: '请先完成认证再发布仪器', icon: 'none' });
      return;
    }

    const tradeModes = tradeModeOptions.filter((item) => item.selected).map((item) => item.value);

    if (!categories.length) {
      wx.showToast({ title: '分类数据尚未加载完成', icon: 'none' });
      return;
    }
    if (!form.name.trim() || !form.location.trim() || !form.desc.trim()) {
      wx.showToast({ title: '请完善名称、城市和科研描述', icon: 'none' });
      return;
    }
    if (tradeModes.includes('租赁') && !/^\d+(\.\d+)?$/.test(form.price.trim())) {
      wx.showToast({ title: '请填写正确的日租价', icon: 'none' });
      return;
    }
    if (tradeModes.includes('出售') && !/^\d+(\.\d+)?$/.test(form.salePrice.trim())) {
      wx.showToast({ title: '请填写正确的买断价格', icon: 'none' });
      return;
    }
    if (tradeModes.includes('租赁') && form.deposit.trim() && !/^\d+(\.\d+)?$/.test(form.deposit.trim())) {
      wx.showToast({ title: '押金格式不正确', icon: 'none' });
      return;
    }

    callService('publishInstrument', {
      ...form,
      images: form.images,
      coverImage: form.images[0] || '',
      category: categories[categoryIndex],
      tradeModes,
      defaultTradeMode: tradeModes[0]
    })
      .then((res) => {
        wx.showModal({
          title: '发布成功',
          content: res.message,
          showCancel: false,
          success: () => {
            wx.navigateTo({ url: '/pages/my-instruments/index' });
          }
        });
      })
      .catch(showError);
  }
});
