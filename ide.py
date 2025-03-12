import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QTabWidget, QFileDialog, QVBoxLayout, QWidget, QMenu, QMenuBar
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt


class IDE(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Simple IDE')
        self.setGeometry(100, 100, 800, 600)

        # Central widget with tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        self.setCentralWidget(self.tabs)

        # Output area
        self.output_area = QTextEdit(self)
        self.output_area.setReadOnly(True)
        self.output_area.setPlaceholderText('Output will appear here...')
        self.output_area.setVisible(False)

        # Menu bar
        self.menu_bar = self.menuBar()
        self.create_menus()

        # Status bar
        self.statusBar().showMessage('Ready')

    def create_menus(self):
        # Create File menu
        file_menu = QMenu('File', self)
        self.menu_bar.addMenu(file_menu)

        open_action = QAction('Open', self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction('Save', self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        close_action = QAction('Close', self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)

        # Create Edit menu
        edit_menu = QMenu('Edit', self)
        self.menu_bar.addMenu(edit_menu)

        run_action = QAction('Run', self)
        run_action.triggered.connect(self.run_code)
        edit_menu.addAction(run_action)

        # Add output area toggle
        toggle_output_action = QAction('Toggle Output', self)
        toggle_output_action.triggered.connect(self.toggle_output)
        edit_menu.addAction(toggle_output_action)

    def open_file(self):
        # Open file and load its content into a new tab
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'Text Files (*.txt);;Python Files (*.py);;All Files (*)')

        if file_name:
            with open(file_name, 'r') as file:
                content = file.read()

            editor = QTextEdit()
            editor.setText(content)
            editor.textChanged.connect(self.mark_modified)
            self.tabs.addTab(editor, file_name)

    def save_file(self):
        # Save the content of the currently selected tab
        current_editor = self.tabs.currentWidget()
        if current_editor:
            file_name, _ = QFileDialog.getSaveFileName(self, 'Save File', '', 'Text Files (*.txt);;Python Files (*.py);;All Files (*)')
            if file_name:
                with open(file_name, 'w') as file:
                    file.write(current_editor.toPlainText())

    def close_tab(self, index):
        # Close the selected tab
        current_editor = self.tabs.widget(index)
        if current_editor:
            # Optionally, check for unsaved changes
            self.tabs.removeTab(index)

    def mark_modified(self):
        # Optionally, mark the tab as modified (you can add additional logic here)
        current_editor = self.tabs.currentWidget()
        if current_editor:
            current_editor.setWindowModified(True)

    def run_code(self):
        # Get the current file's content and "run" it (For example, just print it to output)
        current_editor = self.tabs.currentWidget()
        if current_editor:
            content = current_editor.toPlainText()
            self.output_area.setText(content)
            self.output_area.setVisible(True)
            self.statusBar().showMessage('Code executed successfully')

    def toggle_output(self):
        # Toggle the visibility of the output area
        self.output_area.setVisible(not self.output_area.isVisible())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = IDE()
    window.show()
    sys.exit(app.exec())
