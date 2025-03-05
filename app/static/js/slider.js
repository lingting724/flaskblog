class SliderValidator {
  constructor(element, options = {}) {
    this.element = element
    this.options = {
      successText: options.successText || '验证通过',
      defaultText: options.defaultText || '请向右滑动验证',
      onSuccess: options.onSuccess || function () {},
    }
    this.init()
  }

  init() {
    // 创建滑块元素
    this.createSlider()
    // 绑定事件
    this.bindEvents()
  }

  createSlider() {
    this.container = document.createElement('div')
    this.container.className = 'slider-container'

    this.bg = document.createElement('div')
    this.bg.className = 'slider-bg'

    // 添加进度条元素
    this.progress = document.createElement('div')
    this.progress.className = 'slider-progress'
    this.bg.appendChild(this.progress)

    // 添加文字容器
    this.text = document.createElement('div')
    this.text.className = 'slider-text'
    this.text.textContent = this.options.defaultText
    this.bg.appendChild(this.text)

    this.btn = document.createElement('div')
    this.btn.className = 'slider-btn'
    this.btn.innerHTML = '<i class="fas fa-arrows-alt-h"></i>'

    this.container.appendChild(this.bg)
    this.container.appendChild(this.btn)
    this.element.appendChild(this.container)
  }

  bindEvents() {
    this.btn.addEventListener('mousedown', this.onDragStart.bind(this))
    document.addEventListener('mousemove', this.onDragging.bind(this))
    document.addEventListener('mouseup', this.onDragEnd.bind(this))

    // 移动端支持
    this.btn.addEventListener('touchstart', this.onDragStart.bind(this))
    document.addEventListener('touchmove', this.onDragging.bind(this))
    document.addEventListener('touchend', this.onDragEnd.bind(this))
  }

  onDragStart(e) {
    e.preventDefault()
    this.dragging = true
    this.startX = e.type === 'mousedown' ? e.clientX : e.touches[0].clientX
    this.btnLeft = this.btn.offsetLeft
  }

  onDragging(e) {
    if (!this.dragging) return

    const moveX = e.type === 'mousemove' ? e.clientX : e.touches[0].clientX
    const offsetX = moveX - this.startX
    const newLeft = Math.max(0, Math.min(this.btnLeft + offsetX, this.container.offsetWidth - this.btn.offsetWidth))

    // 更新滑块位置和进度条宽度
    this.btn.style.left = newLeft + 'px'
    this.progress.style.width = newLeft + this.btn.offsetWidth / 2 + 'px'
  }

  onDragEnd() {
    if (!this.dragging) return
    this.dragging = false

    const success = this.btn.offsetLeft > this.container.offsetWidth - this.btn.offsetWidth - 5
    if (success) {
      this.success()
    } else {
      this.reset()
    }
  }

  success() {
    this.container.classList.add('slider-success')
    this.text.textContent = this.options.successText
    this.btn.innerHTML = '<i class="fas fa-check"></i>'
    const finalPosition = this.container.offsetWidth - this.btn.offsetWidth
    this.btn.style.left = finalPosition + 'px'
    this.progress.style.width = finalPosition + this.btn.offsetWidth / 2 + 'px'
    this.options.onSuccess()
  }

  reset() {
    this.container.classList.remove('slider-success')
    this.text.textContent = this.options.defaultText
    this.btn.innerHTML = '<i class="fas fa-arrows-alt-h"></i>'
    this.btn.style.left = '0'
    this.progress.style.width = '0'
  }
}
