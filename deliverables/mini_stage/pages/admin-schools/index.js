const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '操作失败，请稍后重试',
    icon: 'none'
  });
}

Page({
  data: {
    loading: true,
    list: [],
    schoolName: '',
    collegesText: ''
  },
  onShow() {
    this.loadData();
  },
  loadData() {
    this.setData({ loading: true });
    callService('getSchoolList')
      .then((res) => this.setData({ list: res.list, loading: false }))
      .catch((error) => {
        this.setData({ loading: false });
        showError(error);
      });
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onInput(event) {
    this.setData({ [event.currentTarget.dataset.field]: event.detail.value });
  },
  submit() {
    if (!this.data.schoolName.trim() || !this.data.collegesText.trim()) {
      wx.showToast({ title: '请填写学校和学院', icon: 'none' });
      return;
    }
    callService('addSchool', {
      name: this.data.schoolName.trim(),
      colleges: this.data.collegesText
        .split(/[\n、，,]/)
        .map((item) => item.trim())
        .filter(Boolean)
    })
      .then((res) => {
        wx.showModal({ title: '添加成功', content: res.message, showCancel: false });
        this.setData({ schoolName: '', collegesText: '' });
        this.loadData();
      })
      .catch(showError);
  }
});
