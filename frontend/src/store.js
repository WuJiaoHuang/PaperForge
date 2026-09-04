import { reactive } from 'vue'

export const TECH_PRESETS = [
  'SpringBoot', 'Vue', 'Vue3', 'MySQL', 'Redis', 'MyBatis-Plus',
  'Python', 'Django', 'Flask', '小程序', 'React', 'Element Plus',
]
export const DEFAULT_TECHS = ['SpringBoot', 'Vue', 'MySQL', 'Redis']
export const STAGE_NAMES = ['系统设定', '摘要', 'Abstract', '绪论', '相关技术', '需求分析', '系统设计', '系统实现', '系统测试', '总结展望', '参考文献致谢']
export const CHART_POSITIONS = ['第 3 章 需求分析', '第 4 章 系统设计', '第 5 章 系统实现', '第 6 章 系统测试', '文末']
export const HISTORY_KEY = 'paperforge_v1_history'

export const DEFAULT_CHART_TYPES = [
  { type: 'er', label: 'E-R 图', hint: '粘贴 SQL 建表语句(CREATE TABLE …),留空则使用系统设定的数据表' },
  { type: 'flow', label: '流程图', hint: '按顺序描述步骤,每行一步;留空则生成默认业务流程' },
  { type: 'architecture', label: '系统架构图', hint: '每行一层(如:用户层:浏览器);留空则按技术栈生成' },
  { type: 'module', label: '功能模块图', hint: '可留空,默认使用系统设定的功能模块' },
  { type: 'usecase', label: '系统用例图', hint: '可留空,默认使用系统设定的角色与功能' },
  { type: 'sequence', label: '时序图', hint: '每行格式:角色A -> 角色B: 消息;留空则生成默认交互时序' },
]

export const store = reactive({
  aiAvailable: false,
  useAi: false,
  techs: [...DEFAULT_TECHS],
  customTechs: [],
  title: '',
  keywords: '',
  wordLevel: 'medium',
  style: '严谨学术',
  requirements: '',
  busy: false,
  view: 'topic',
  topics: [],
  batch: 0,
  selectedTopic: null,
  topicHint: '不确定写什么?直接点击「一键推荐」,系统将推荐 4 个备选题目',
  topicNote: '',
  refreshVisible: false,
  current: 0,
  total: 11,
  stageText: '准备中…',
  progressPct: 2,
  liveDesign: null,
  liveChapters: [],
  payload: null,
  renderedSeq: [],
  chartTypes: [...DEFAULT_CHART_TYPES],
  chartExtras: [],
  chartImages: {},
  chartVersion: 0,
  currentPaperId: '',
  diagrams: [],
  activeDiagram: null,
  diagramEditorOpen: false,
  diagramLoading: false,
  diagramSaving: false,
  diagramMessage: '',
  history: [],
})
