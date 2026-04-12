const { callService } = require('../../utils/api');

function showError(error) {
  wx.showToast({
    title: (error && error.message) || '项目发布失败',
    icon: 'none'
  });
}

Page({
  data: {
    form: {
      title: '',
      company: '',
      domain: '',
      budget: '',
      duration: '',
      needs: ''
    }
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  onInput(event) {
    const { field } = event.currentTarget.dataset;
    this.setData({
      [`form.${field}`]: event.detail.value
    });
  },
  submitProject() {
    const { title, company, domain, budget, duration, needs } = this.data.form;
    if (!title.trim() || !company.trim() || !needs.trim()) {
      wx.showToast({ title: '请补充核心项目信息', icon: 'none' });
      return;
    }

    callService('publishProject', {
      title,
      company,
      domain,
      budget,
      duration,
      needs
    })
      .then((res) => {
        wx.showModal({
          title: '发布成功',
          content: `${res.message}\n项目编号：${res.projectId}`,
          showCancel: false,
          success: () => {
            wx.navigateBack({ delta: 1 });
          }
        });
      })
      .catch(showError);
  }
});
