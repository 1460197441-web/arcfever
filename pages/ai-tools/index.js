const { callService } = require('../../utils/api');
const { aiTools } = require('../../utils/mock');

Page({
  data: {
    tools: aiTools,
    currentToolId: aiTools[0].id,
    goal: '',
    dataset: '',
    result: null
  },
  goBack() {
    wx.navigateBack({ delta: 1 });
  },
  chooseTool(event) {
    this.setData({
      currentToolId: event.currentTarget.dataset.id
    });
  },
  onInput(event) {
    const { field } = event.currentTarget.dataset;
    this.setData({ [field]: event.detail.value });
  },
  submitTask() {
    const { currentToolId, goal, dataset } = this.data;
    if (!goal.trim()) {
      wx.showToast({ title: '请先填写分析目标', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '分析中...' });
    callService('submitAiTask', {
      toolId: currentToolId,
      goal,
      dataset
    })
      .then((result) => {
        this.setData({ result });
      })
      .finally(() => {
        wx.hideLoading();
      });
  }
});
