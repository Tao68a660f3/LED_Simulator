from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import uuid  # 添加uuid用于生成唯一标识


class FontCategory:
    """字体分类数据类"""
    def __init__(self, category_type, category_name, dir_path):
        self.id = str(uuid.uuid4())  # 添加唯一ID
        self.type = category_type          # FONT
        self.category_name = category_name  # ASCII_FONT, SYS_FONT, HZK_FONT
        self.dir_path = dir_path            # 目录路径
        self.fonts = []                      # 字体列表 [(filename, display_name, raw_line)]
        self.comments_before = []             # 分类前的注释
        self.comments_after = []               # 分类后的空行/注释
        self.raw_category_line = ""            # 原始分类行
        
    def get_display_name(self):
        """获取显示名称（包含类型和路径）"""
        type_names = {
            'ASCII_FONT': 'ASCII字体',
            'SYS_FONT': '系统字体',
            'HZK_FONT': 'HZK汉字',
        }
        base_name = type_names.get(self.category_name, self.category_name)
        
        # 从路径中提取最后一部分作为区分
        if 'bmpFont' in self.dir_path:
            return f"{base_name} - 位图"
        elif 'fontFont' in self.dir_path:
            return f"{base_name} - 文本"
        elif 'truetypeFont' in self.dir_path:
            return f"{base_name} - TrueType"
        elif 'hzkFont' in self.dir_path:
            return f"{base_name} - 点阵"
        elif 'binAsc' in self.dir_path:
            return f"{base_name} - 二进制"
        elif 'Windows/Fonts' in self.dir_path:
            return f"{base_name} - 系统"
        else:
            # 如果没有特殊标识，使用路径的最后一部分
            path_parts = self.dir_path.strip('/\\').split('/')[-1].split('\\')[-1]
            if path_parts:
                return f"{base_name} - {path_parts}"
            return base_name

class FontManagerApp(QMainWindow):
    def __init__(self, MainWindow):
        super().__init__(MainWindow)
        self.current_file = "./resources/font.info"  # 默认文件名
        self.categories = []  # 改为列表，保持顺序
        self.file_header_comments = []     # 文件头注释
        self.file_footer_comments = []     # 文件尾注释
        self.modified = False              # 是否有未保存的修改
        
        self.init_ui()
        self.load_file()
        
    def init_ui(self):
        self.setWindowTitle("字体管理器")
        self.setGeometry(100, 100, 1000, 700)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 中央分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧分类导航
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderLabel("字体分类")
        self.category_tree.setMinimumWidth(300)
        self.category_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.category_tree.customContextMenuRequested.connect(self.show_category_menu)
        self.category_tree.itemClicked.connect(self.on_category_selected)
        
        # 右侧字体表格
        self.font_table = QTableWidget()
        self.font_table.setColumnCount(4)
        self.font_table.setHorizontalHeaderLabels(['文件名', '显示名称', '操作', '原始行'])
        self.font_table.horizontalHeader().setStretchLastSection(False)
        self.font_table.setColumnWidth(0, 200)
        self.font_table.setColumnWidth(1, 200)
        self.font_table.setColumnWidth(2, 150)
        self.font_table.hideColumn(3)  # 隐藏原始行列
        
        self.font_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.font_table.customContextMenuRequested.connect(self.show_font_menu)
        
        # 右侧布局
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 分类信息栏
        self.info_frame = QFrame()
        self.info_frame.setFrameStyle(QFrame.StyledPanel)
        info_layout = QHBoxLayout(self.info_frame)
        
        self.category_type_label = QLabel("类型: ")
        self.category_path_label = QLabel("路径: ")
        self.category_path_label.setStyleSheet("color: #666;")
        
        info_layout.addWidget(self.category_type_label)
        info_layout.addWidget(self.category_path_label)
        info_layout.addStretch()
        
        # 添加字体按钮
        self.add_font_btn = QPushButton("➕ 添加字体")
        self.add_font_btn.clicked.connect(self.add_font)
        info_layout.addWidget(self.add_font_btn)
        
        right_layout.addWidget(self.info_frame)
        right_layout.addWidget(self.font_table)
        
        # 状态栏
        self.status_label = QLabel("就绪")
        self.statusBar().addWidget(self.status_label)
        
        splitter.addWidget(self.category_tree)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])
        
        self.setCentralWidget(splitter)
        
        # 连接表格双击编辑
        self.font_table.itemDoubleClicked.connect(self.on_font_double_clicked)
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        open_action = QAction("打开", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("保存", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 分类菜单
        category_menu = menubar.addMenu("分类")
        
        add_category_action = QAction("新增分类", self)
        add_category_action.triggered.connect(self.add_category)
        category_menu.addAction(add_category_action)
        
    def create_tool_bar(self):
        toolbar = self.addToolBar("工具栏")
        
        save_btn = QAction("💾 保存", self)
        save_btn.triggered.connect(self.save_file)
        toolbar.addAction(save_btn)
        
        toolbar.addSeparator()
        
        add_category_btn = QAction("📁 新建分类", self)
        add_category_btn.triggered.connect(self.add_category)
        toolbar.addAction(add_category_btn)
        
    def load_file(self):
        """加载字体文件"""
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            self.parse_file(lines)
            self.update_category_tree()
            self.status_label.setText(f"已加载: {self.current_file}")
            self.modified = False
        except FileNotFoundError:
            # 文件不存在，创建默认结构
            self.create_default_structure()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载文件失败: {e}")
            
    def parse_file(self, lines):
        """解析文件内容"""
        self.categories.clear()
        self.file_header_comments = []
        self.file_footer_comments = []
        
        i = 0
        # 收集文件头注释
        while i < len(lines):
            line = lines[i].rstrip('\n')
            if line.startswith('#') or line.strip() == '':
                self.file_header_comments.append(line)
                i += 1
            else:
                break
        
        # 解析分类
        while i < len(lines):
            line = lines[i].rstrip('\n')
            
            # 检查是否是分类定义行
            if line.startswith('FONT,'):
                parts = line.split(',')
                if len(parts) >= 3:
                    category_type = parts[0]  # FONT
                    category_name = parts[1]   # ASCII_FONT
                    dir_part = parts[2]         # DIR:./resources/
                    
                    # 提取目录路径并确保有斜杠
                    dir_path = dir_part[4:] if dir_part.startswith('DIR:') else ''
                    if dir_path and not dir_path.endswith('/') and not dir_path.endswith('\\'):
                        dir_path += '/'  # 统一添加斜杠
                    
                    category = FontCategory(category_type, category_name, dir_path)
                    category.raw_category_line = line
                    
                    i += 1
                    
                    # 收集该分类下的内容
                    while i < len(lines):
                        next_line = lines[i].rstrip('\n')
                        
                        if next_line.startswith('FONT,'):
                            break
                        
                        if next_line.startswith('#') or next_line.strip() == '':
                            category.comments_after.append(next_line)
                        elif ',' in next_line:
                            font_parts = next_line.split(',')
                            if len(font_parts) >= 2:
                                filename = font_parts[0].strip()
                                display_name = font_parts[1].strip()
                                category.fonts.append((filename, display_name, next_line))
                        
                        i += 1
                    
                    self.categories.append(category)
                    continue
            i += 1
        
        # 文件尾注释
        while i < len(lines):
            line = lines[i].rstrip('\n')
            self.file_footer_comments.append(line)
            i += 1
            
    def create_default_structure(self):
        """创建默认的文件结构"""
        default_content = """# 字体信息文件

# 位图ASCII字体
FONT,ASCII_FONT,DIR:./resources/bmpFont/,
ASCII_8-13_COURE.bmp,ASCII_8-13_COURE,
ASCII_8-16.bmp,ASCII_8-16,


# 16进制文本ASCII字体
FONT,ASCII_FONT,DIR:./resources/fontFont/,
ASC0704.font,ASC0704,
ASC0705.font,ASC0705,


# 携带的ttc、ttf字体
FONT,SYS_FONT,DIR:./resources/truetypeFont/,
simsun.ttc,旧宋体,
SimSun-18030.ttf,宋体18030,
Song1.ttf,宋一,
7segments.ttf,数码管体,

# 安装的系统字体
FONT,SYS_FONT,DIR:C:/Windows/Fonts/,
arial.ttf,Arial,
ARIALN.TTF,ARIALN,


# HZK汉字
FONT,HZK_FONT,DIR:./resources/hzkFont/,
hzk16.hzk,HZK16,
hzk16s.hzk,HZK16宋体,


# 使用生成程序生成的二进制ASCII字体
FONT,ASCII_FONT,DIR:./resources/binAsc/,
ASCE14.bin,14 px bin字体实验,
"""
        lines = default_content.split('\n')
        self.parse_file([line + '\n' for line in lines])
        
    def update_category_tree(self):
        """更新分类树"""
        self.category_tree.clear()
        
        for category in self.categories:
            display_name = category.get_display_name()
            item = QTreeWidgetItem(self.category_tree)
            item.setText(0, f"{display_name} ({len(category.fonts)})")
            item.setData(0, Qt.UserRole, category.id)  # 使用唯一ID作为数据
            
            # 设置图标
            if 'ASCII' in category.category_name:
                if 'bmp' in category.dir_path:
                    item.setIcon(0, self.style().standardIcon(QStyle.SP_DialogResetButton))
                elif 'bin' in category.dir_path:
                    item.setIcon(0, self.style().standardIcon(QStyle.SP_FileIcon))
                else:
                    item.setIcon(0, self.style().standardIcon(QStyle.SP_FileDialogContentsView))
            elif 'SYS' in category.category_name:
                item.setIcon(0, self.style().standardIcon(QStyle.SP_DesktopIcon))
            elif 'HZK' in category.category_name:
                item.setIcon(0, self.style().standardIcon(QStyle.SP_FileDialogListView))
        
        self.category_tree.sortItems(0, Qt.AscendingOrder)
        
    def on_category_selected(self, item, column):
        """分类选择事件"""
        category_id = item.data(0, Qt.UserRole)
        # 查找对应的分类
        for category in self.categories:
            if category.id == category_id:
                self.show_category_fonts(category)
                break
            
    def show_category_fonts(self, category):
        """显示分类下的字体"""
        self.font_table.setRowCount(0)
        
        # 更新分类信息
        self.category_type_label.setText(f"类型: {category.category_name}")
        self.category_path_label.setText(f"路径: {category.dir_path}")
        
        # 保存当前选中的分类ID到表格的属性中
        self.font_table.setProperty("current_category_id", category.id)
        
        for i, (filename, display_name, raw_line) in enumerate(category.fonts):
            self.font_table.insertRow(i)
            
            # 文件名
            name_item = QTableWidgetItem(filename)
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            self.font_table.setItem(i, 0, name_item)
            
            # 显示名称
            display_item = QTableWidgetItem(display_name)
            display_item.setFlags(display_item.flags() | Qt.ItemIsEditable)
            self.font_table.setItem(i, 1, display_item)
            
            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(2)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(30, 25)
            edit_btn.setToolTip("编辑")
            edit_btn.clicked.connect(lambda checked, row=i: self.edit_font(row))
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(30, 25)
            delete_btn.setToolTip("删除")
            delete_btn.clicked.connect(lambda checked, row=i: self.delete_font(row))
            
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(delete_btn)
            
            self.font_table.setCellWidget(i, 2, btn_widget)
            
            # 原始行（隐藏）
            raw_item = QTableWidgetItem(raw_line)
            self.font_table.setItem(i, 3, raw_item)
            
    def get_current_category(self):
        """获取当前选中的分类"""
        current_item = self.category_tree.currentItem()
        if not current_item:
            return None
            
        category_id = current_item.data(0, Qt.UserRole)
        for category in self.categories:
            if category.id == category_id:
                return category
        return None
        
    def add_category(self):
        """新增分类"""
        dialog = QDialog(self)
        dialog.setWindowTitle("新增分类")
        dialog.setModal(True)
        
        layout = QFormLayout(dialog)
        
        type_combo = QComboBox()
        type_combo.addItems(['ASCII_FONT', 'SYS_FONT', 'HZK_FONT'])
        layout.addRow("分类类型:", type_combo)
        
        path_edit = QLineEdit("./resources/")
        layout.addRow("目录路径:", path_edit)
        
        # 添加备注输入
        comment_edit = QTextEdit()
        comment_edit.setMaximumHeight(60)
        comment_edit.setPlaceholderText("可选的分类注释...")
        layout.addRow("注释:", comment_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            category_type = "FONT"
            category_name = type_combo.currentText()
            dir_path = path_edit.text()
            
            # 确保目录路径以斜杠结尾
            if dir_path and not dir_path.endswith('/') and not dir_path.endswith('\\'):
                dir_path += '/'
            
            comment = comment_edit.toPlainText()
            
            category = FontCategory(category_type, category_name, dir_path)
            category.raw_category_line = f"{category_type},{category_name},DIR:{dir_path},"
            
            # 添加注释
            if comment.strip():
                category.comments_before = [f"# {comment}"]
            
            self.categories.append(category)
            
            self.update_category_tree()
            self.modified = True
            self.status_label.setText("已添加新分类")
            
    def add_font(self):
        """添加字体到当前分类"""
        category = self.get_current_category()
        if not category:
            QMessageBox.warning(self, "警告", "请先选择一个分类")
            return
            
        # 简单的输入对话框
        filename, ok1 = QInputDialog.getText(self, "添加字体", "文件名:")
        if not ok1 or not filename:
            return
            
        display_name, ok2 = QInputDialog.getText(self, "添加字体", "显示名称:")
        if not ok2:
            return
            
        # 添加到分类
        raw_line = f"{filename},{display_name},"
        category.fonts.append((filename, display_name, raw_line))
        
        # 更新显示
        self.show_category_fonts(category)
        self.update_category_tree()  # 更新计数
        self.modified = True
        
    def edit_font(self, row):
        """编辑字体"""
        category = self.get_current_category()
        if not category or row >= len(category.fonts):
            return
            
        filename, display_name, raw_line = category.fonts[row]
        
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑字体")
        
        layout = QFormLayout(dialog)
        
        filename_edit = QLineEdit(filename)
        layout.addRow("文件名:", filename_edit)
        
        display_edit = QLineEdit(display_name)
        layout.addRow("显示名称:", display_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            new_filename = filename_edit.text()
            new_display = display_edit.text()
            new_raw = f"{new_filename},{new_display},"
            
            category.fonts[row] = (new_filename, new_display, new_raw)
            
            self.show_category_fonts(category)
            self.modified = True
            
    def delete_font(self, row):
        """删除字体"""
        reply = QMessageBox.question(self, "确认", "确定要删除这个字体吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            category = self.get_current_category()
            if category and row < len(category.fonts):
                del category.fonts[row]
                self.show_category_fonts(category)
                self.update_category_tree()
                self.modified = True
                
    def on_font_double_clicked(self, item):
        """双击表格编辑"""
        if item.column() < 2:  # 只允许编辑文件名和显示名称
            row = item.row()
            self.edit_font(row)
            
    def show_category_menu(self, position):
        """显示分类右键菜单"""
        menu = QMenu()
        
        add_action = menu.addAction("新增分类")
        add_action.triggered.connect(self.add_category)
        
        item = self.category_tree.itemAt(position)
        if item:
            menu.addSeparator()
            rename_action = menu.addAction("重命名分类")
            rename_action.triggered.connect(lambda: self.rename_category(item))
            
            delete_action = menu.addAction("删除分类")
            delete_action.triggered.connect(lambda: self.delete_category(item))
            
        menu.exec_(self.category_tree.viewport().mapToGlobal(position))
        
    def rename_category(self, item):
        """重命名分类"""
        category_id = item.data(0, Qt.UserRole)
        category = None
        for cat in self.categories:
            if cat.id == category_id:
                category = cat
                break
                
        if not category:
            return
            
        new_name, ok = QInputDialog.getText(self, "重命名分类", 
                                           "新分类类型 (ASCII_FONT/SYS_FONT/HZK_FONT):",
                                           text=category.category_name)
        if ok and new_name:
            category.category_name = new_name
            # 更新原始分类行
            category.raw_category_line = f"{category.type},{new_name},DIR:{category.dir_path},"
            
            self.update_category_tree()
            self.modified = True
            
    def delete_category(self, item):
        """删除分类"""
        reply = QMessageBox.question(self, "确认", 
                                     "确定要删除这个分类吗？分类下的所有字体也会被删除。",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            category_id = item.data(0, Qt.UserRole)
            for i, category in enumerate(self.categories):
                if category.id == category_id:
                    del self.categories[i]
                    break
                    
            self.update_category_tree()
            self.font_table.setRowCount(0)
            self.modified = True
                
    def show_font_menu(self, position):
        """显示字体右键菜单"""
        menu = QMenu()
        
        add_action = menu.addAction("添加字体")
        add_action.triggered.connect(self.add_font)
        
        item = self.font_table.itemAt(position)
        if item:
            row = item.row()
            menu.addSeparator()
            edit_action = menu.addAction("编辑")
            edit_action.triggered.connect(lambda: self.edit_font(row))
            
            delete_action = menu.addAction("删除")
            delete_action.triggered.connect(lambda: self.delete_font(row))
            
        menu.exec_(self.font_table.viewport().mapToGlobal(position))
        
    def save_file(self):
        """保存文件"""
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                # 写入文件头注释
                for comment in self.file_header_comments:
                    f.write(comment + '\n')
                
                # 写入分类
                for i, category in enumerate(self.categories):
                    # 确保目录路径以 / 结尾
                    dir_path = category.dir_path
                    if dir_path and not dir_path.endswith('/') and not dir_path.endswith('\\'):
                        dir_path += '/'  # 统一使用正斜杠
                    
                    # 重新构建分类行
                    category.raw_category_line = f"{category.type},{category.category_name},DIR:{dir_path},"
                    
                    # 写入分类行
                    f.write(category.raw_category_line + '\n')
                    
                    # 写入字体
                    for filename, display_name, raw_line in category.fonts:
                        f.write(raw_line + '\n')
                    
                    # 写入分类后的注释/空行
                    for comment in category.comments_after:
                        f.write(comment + '\n')
                
                # 写入文件尾注释
                for comment in self.file_footer_comments:
                    f.write(comment + '\n')
                        
            self.modified = False
            self.status_label.setText(f"已保存: {self.current_file}")
            QMessageBox.information(self, "成功", "文件保存成功！")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存文件失败: {e}")
            
    def open_file(self):
        """打开文件"""
        if self.modified:
            reply = QMessageBox.question(self, "保存", 
                                         "当前文件已修改，是否保存？",
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return
                
        file_path, _ = QFileDialog.getOpenFileName(self, "打开字体文件", 
                                                   "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            self.current_file = file_path
            self.load_file()
            
    def closeEvent(self, event):
        """关闭事件"""
        if self.modified:
            reply = QMessageBox.question(self, "保存", 
                                         "文件已修改，是否保存？",
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.save_file()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

