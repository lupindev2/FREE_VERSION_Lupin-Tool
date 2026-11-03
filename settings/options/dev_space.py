
import sys
import os
import json
import shutil
import subprocess
import traceback
from pathlib import Path

from PySide6.QtCore import (
    Qt, QDir, QTimer, QProcess, QSize, Signal
)
from PySide6.QtGui import (
    QColor, QFont, QTextCharFormat, QSyntaxHighlighter,
    QTextCursor, QAction, QKeySequence
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QSplitter, QTreeView, QFileSystemModel,
    QTabWidget, QPlainTextEdit, QTextEdit, QToolBar,
    QStatusBar, QFileDialog, QMessageBox, QInputDialog,
    QLineEdit, QPushButton, QLabel, QDockWidget,
    QFrame, QMenu, QStyle, QToolButton, QDialog,
    QDialogButtonBox
)


                                                           
       
                                                           

STYLE = """
* {
    font-family: "Segoe UI";
    font-size: 13px;
}

QMainWindow, QWidget {
    background: #171a23;
    color: #dce1ed;
}

QMenuBar {
    background: #171a23;
    color: #dce1ed;
    padding: 5px;
}

QMenuBar::item:selected {
    background: #292f40;
    border-radius: 5px;
}

QMenu {
    background: #222735;
    border: 1px solid #343c50;
    padding: 5px;
}

QMenu::item {
    padding: 7px 28px;
    border-radius: 4px;
}

QMenu::item:selected {
    background: #35445f;
}

QToolBar {
    background: #1b202c;
    border: none;
    spacing: 6px;
    padding: 7px;
}

QToolButton {
    color: #dce1ed;
    background: transparent;
    border: none;
    padding: 7px;
    border-radius: 6px;
}

QToolButton:hover {
    background: #30394d;
}

QTreeView {
    background: #191e29;
    border: none;
    outline: none;
    padding: 5px;
    selection-background-color: #344968;
    alternate-background-color: #1c2230;
}

QTreeView::item {
    height: 27px;
    padding-left: 4px;
}

QTreeView::item:hover {
    background: #262e3d;
}

QTabWidget::pane {
    border: none;
    background: #151922;
}

QTabBar::tab {
    background: #1d2330;
    color: #909bad;
    padding: 10px 18px;
    border-right: 1px solid #303748;
    min-width: 95px;
}

QTabBar::tab:selected {
    background: #151922;
    color: #ffffff;
    border-top: 2px solid #58a6ff;
}

QTabBar::tab:hover {
    background: #282f3e;
}

QPlainTextEdit {
    background: #151922;
    color: #dce1ed;
    border: none;
    selection-background-color: #354c70;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 14px;
}

QLineEdit {
    background: #252c3b;
    color: #ffffff;
    border: 1px solid #39445b;
    border-radius: 6px;
    padding: 8px;
}

QPushButton {
    background: #29364c;
    color: #e4eaf5;
    border: 1px solid #3b4b65;
    border-radius: 6px;
    padding: 7px 12px;
}

QPushButton:hover {
    background: #354b6a;
}

QPushButton:pressed {
    background: #24364e;
}

QStatusBar {
    background: #263b59;
    color: white;
}

QDockWidget {
    color: #dce1ed;
    font-weight: bold;
}

QScrollBar:vertical {
    background: #171d29;
    width: 10px;
}

QScrollBar::handle:vertical {
    background: #46516a;
    border-radius: 4px;
    min-height: 25px;
}

QScrollBar:horizontal {
    background: #171d29;
    height: 10px;
}

QScrollBar::handle:horizontal {
    background: #46516a;
    border-radius: 4px;
}

QSplitter::handle {
    background: #303849;
}

QSplitter::handle:hover {
    background: #58a6ff;
}
"""


                                                           
                    
                                                           

class PythonHighlighter(QSyntaxHighlighter):

    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        def add(pattern, color, bold=False, italic=False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))

            if bold:
                fmt.setFontWeight(QFont.Weight.Bold)

            if italic:
                fmt.setFontItalic(True)

            self.rules.append((pattern, fmt))

        keywords = (
            "and as assert async await break class continue "
            "def del elif else except False finally for from "
            "global if import in is lambda None nonlocal not "
            "or pass raise return True try while with yield"
        ).split()

        for word in keywords:
            add(r"\b" + word + r"\b", "#c792ea", True)

        builtins = (
            "print len range str int float list dict set "
            "tuple open super self isinstance enumerate "
            "zip map filter sum min max type object"
        ).split()

        for word in builtins:
            add(r"\b" + word + r"\b", "#82aaff")

        add(r"#[^\n]*", "#82936f", italic=True)
        add(r"\b\d+(\.\d+)?\b", "#f78c6c")
        add(r"@[A-Za-z_]\w*", "#ffcb6b")

        add(r"\bdef\s+\w+", "#82aaff", True)
        add(r"\bclass\s+\w+", "#ffcb6b", True)

        add(
            r'"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\'',
            "#c3e88d"
        )

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            import re
            for match in re.finditer(pattern, text):
                self.setFormat(
                    match.start(),
                    match.end() - match.start(),
                    fmt
                )


                                                           
        
                                                           

class CodeEditor(QPlainTextEdit):

    def __init__(self, path=None):
        super().__init__()

        self.path = Path(path) if path else None
        self.modified = False

        self.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.NoWrap
        )

        self.setTabStopDistance(
            self.fontMetrics().horizontalAdvance(" ") * 4
        )

        self.setFont(QFont("Cascadia Code", 11))

        self.highlighter = PythonHighlighter(
            self.document()
        )

        self.textChanged.connect(self.on_modified)

    def on_modified(self):
        self.modified = True

    def load(self, path):
        path = Path(path)

        try:
            content = path.read_text(
                encoding="utf-8",
                errors="replace"
            )

            self.blockSignals(True)
            self.setPlainText(content)
            self.blockSignals(False)

            self.path = path
            self.modified = False
            self.document().setModified(False)

            return True

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible d'ouvrir le fichier :\n{e}"
            )
            return False

    def save(self, path=None):

        target = Path(path) if path else self.path

        if target is None:
            return self.save_as()

        try:
            target.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            target.write_text(
                self.toPlainText(),
                encoding="utf-8",
                newline=""
            )

            self.path = target
            self.modified = False
            self.document().setModified(False)

            return True

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur de sauvegarde",
                str(e)
            )
            return False

    def save_as(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer sous",
            str(self.path.parent if self.path else Path.home()),
            "Tous les fichiers (*.*)"
        )

        if not path:
            return False

        return self.save(Path(path))


                                                           
           
                                                           

class NexusCode(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("lupin Code")
        self.resize(1450, 900)

        self.workspace = Path.home()

        self.process = None

        self.setup_ui()
        self.setup_menus()
        self.setup_shortcuts()

        self.statusBar().showMessage(
            "lupin Code"
        )

                                                           
               
                                                           

    def setup_ui(self):

        central = QWidget()
        layout = QVBoxLayout(central)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.splitter = QSplitter(
            Qt.Orientation.Horizontal
        )

                     

        explorer = QWidget()
        explorer.setMinimumWidth(190)
        explorer.setMaximumWidth(430)

        explorer_layout = QVBoxLayout(explorer)
        explorer_layout.setContentsMargins(8, 10, 8, 8)

        header = QHBoxLayout()

        title = QLabel("EXPLORATEUR")
        title.setStyleSheet(
            "font-weight: bold; color: #91a0b9;"
            "padding: 6px;"
        )

        header.addWidget(title)
        header.addStretch()

        self.explorer_buttons = []

        for icon, tip, callback in [
            ("📄", "Nouveau fichier", self.new_file),
            ("📁", "Nouveau dossier", self.new_folder),
            ("↻", "Actualiser", self.refresh_tree),
        ]:
            btn = QToolButton()
            btn.setText(icon)
            btn.setToolTip(tip)
            btn.clicked.connect(callback)
            header.addWidget(btn)
            self.explorer_buttons.append(btn)

        explorer_layout.addLayout(header)

        self.workspace_label = QLabel(
            str(self.workspace)
        )
        self.workspace_label.setStyleSheet(
            "color: #58a6ff; padding: 5px;"
        )

        explorer_layout.addWidget(
            self.workspace_label
        )

        self.model = QFileSystemModel()
        self.model.setFilter(
            QDir.Filter.AllDirs
            | QDir.Filter.Files
            | QDir.Filter.NoDotAndDotDot
        )

        self.model.setRootPath(
            str(self.workspace)
        )

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(
            self.model.index(str(self.workspace))
        )

        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(17)

        for column in range(1, 4):
            self.tree.hideColumn(column)

        self.tree.doubleClicked.connect(
            self.tree_open
        )

        self.tree.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )

        self.tree.customContextMenuRequested.connect(
            self.tree_context_menu
        )

        explorer_layout.addWidget(self.tree)

        self.splitter.addWidget(explorer)

                

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)

        self.tabs.tabCloseRequested.connect(
            self.close_tab
        )

        self.tabs.currentChanged.connect(
            self.update_status
        )

        self.splitter.addWidget(self.tabs)

        self.splitter.setSizes([270, 1100])

        layout.addWidget(self.splitter)

                    

        self.search_widget = QWidget()
        search_layout = QHBoxLayout(
            self.search_widget
        )

        search_layout.setContentsMargins(8, 5, 8, 5)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Rechercher dans le fichier..."
        )

        self.search_input.returnPressed.connect(
            self.find_next
        )

        next_btn = QPushButton("Suivant")
        next_btn.clicked.connect(self.find_next)

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(
            self.search_widget.hide
        )

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(next_btn)
        search_layout.addWidget(close_btn)

        self.search_widget.hide()
        layout.addWidget(self.search_widget)

        self.setCentralWidget(central)

                  

        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setMaximumBlockCount(3000)

        self.terminal_dock = QDockWidget(
            "TERMINAL / SORTIE",
            self
        )

        self.terminal_dock.setWidget(
            self.terminal
        )

        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea,
            self.terminal_dock
        )

        self.terminal_dock.hide()

        self.setStatusBar(QStatusBar())

        self.create_toolbar()

                                                           
             
                                                           

    def create_toolbar(self):

        toolbar = QToolBar("lupin Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(19, 19))

        self.addToolBar(toolbar)

        actions = [
            ("Ouvrir", self.open_file,
             QStyle.StandardPixmap.SP_DialogOpenButton),

            ("Nouveau", self.new_file,
             QStyle.StandardPixmap.SP_FileIcon),

            ("Enregistrer", self.save_file,
             QStyle.StandardPixmap.SP_DialogSaveButton),

            ("Enregistrer sous", self.save_as,
             QStyle.StandardPixmap.SP_DialogSaveButton),

            ("Exécuter", self.run_file,
             QStyle.StandardPixmap.SP_MediaPlay),

            ("Terminal", self.toggle_terminal,
             QStyle.StandardPixmap.SP_ComputerIcon),
        ]

        for label, callback, icon_type in actions:

            action = QAction(
                self.style().standardIcon(icon_type),
                label,
                self
            )

            action.triggered.connect(callback)
            toolbar.addAction(action)

                                                           
           
                                                           

    def setup_menus(self):

        file_menu = self.menuBar().addMenu("Fichier")

        self.add_action(
            file_menu, "Nouveau fichier",
            self.new_file, "Ctrl+N"
        )

        self.add_action(
            file_menu, "Ouvrir un fichier",
            self.open_file, "Ctrl+O"
        )

        self.add_action(
            file_menu, "Ouvrir un dossier",
            self.open_folder, "Ctrl+K"
        )

        file_menu.addSeparator()

        self.add_action(
            file_menu, "Importer un fichier",
            self.import_file
        )

        self.add_action(
            file_menu, "Exporter une copie",
            self.export_file
        )

        file_menu.addSeparator()

        self.add_action(
            file_menu, "Enregistrer",
            self.save_file, "Ctrl+S"
        )

        self.add_action(
            file_menu, "Enregistrer sous",
            self.save_as, "Ctrl+Shift+S"
        )

        file_menu.addSeparator()

        self.add_action(
            file_menu, "Quitter",
            self.close, "Alt+F4"
        )

        edit_menu = self.menuBar().addMenu("Édition")

        self.add_action(
            edit_menu, "Annuler",
            lambda: self.editor().undo(), "Ctrl+Z"
        )

        self.add_action(
            edit_menu, "Rétablir",
            lambda: self.editor().redo(), "Ctrl+Y"
        )

        self.add_action(
            edit_menu, "Rechercher",
            self.show_search, "Ctrl+F"
        )

        self.add_action(
            edit_menu, "Tout sélectionner",
            lambda: self.editor().selectAll(), "Ctrl+A"
        )

        view_menu = self.menuBar().addMenu("Affichage")

        self.add_action(
            view_menu, "Afficher / masquer terminal",
            self.toggle_terminal, "Ctrl+J"
        )

        self.add_action(
            view_menu, "Afficher explorateur",
            self.toggle_explorer, "Ctrl+B"
        )

        run_menu = self.menuBar().addMenu("Exécution")

        self.add_action(
            run_menu, "Exécuter le fichier",
            self.run_file, "F5"
        )

        self.add_action(
            run_menu, "Arrêter",
            self.stop_process, "Shift+F5"
        )

        help_menu = self.menuBar().addMenu("Aide")

        self.add_action(
            help_menu, "À propos",
            self.about
        )

    def add_action(
        self, menu, name, callback, shortcut=None
    ):

        action = QAction(name, self)

        if shortcut:
            action.setShortcut(QKeySequence(shortcut))

        action.triggered.connect(callback)
        menu.addAction(action)

        return action

    def setup_shortcuts(self):

        self.shortcut_find = QAction(self)
        self.shortcut_find.setShortcut("Ctrl+F")
        self.shortcut_find.triggered.connect(
            self.show_search
        )

        self.addAction(self.shortcut_find)

                                                           
                    
                                                           

    def editor(self):

        widget = self.tabs.currentWidget()

        if isinstance(widget, CodeEditor):
            return widget

        return None

    def find_tab(self, path):

        path = Path(path).resolve()

        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)

            if editor.path and editor.path.resolve() == path:
                return i

        return -1

    def add_editor(self, path=None, content=None):

        editor = CodeEditor(path)

        if content is not None:
            editor.setPlainText(content)
            editor.modified = True

        elif path:
            if not editor.load(path):
                return None

        name = (
            Path(path).name if path
            else "Sans titre"
        )

        index = self.tabs.addTab(editor, name)
        self.tabs.setCurrentIndex(index)

        editor.textChanged.connect(
            lambda e=editor: self.update_tab_title(e)
        )

        editor.cursorPositionChanged.connect(
            self.update_status
        )

        return editor

    def update_tab_title(self, editor):

        index = self.tabs.indexOf(editor)

        if index < 0:
            return

        name = (
            editor.path.name if editor.path
            else "Sans titre"
        )

        if editor.modified:
            name = "● " + name

        self.tabs.setTabText(index, name)

    def update_status(self, *args):

        editor = self.editor()

        if editor is None:
            return

        cursor = editor.textCursor()

        line = cursor.blockNumber() + 1
        col = cursor.positionInBlock() + 1

        self.statusBar().showMessage(
            f"Ln {line}   Col {col}   |   "
            f"UTF-8   |   Python / Texte"
        )

    def confirm_save(self, editor):

        if not editor.modified:
            return True

        name = (
            editor.path.name if editor.path
            else "Sans titre"
        )

        answer = QMessageBox.question(
            self,
            "Modifications non enregistrées",
            f"Enregistrer les modifications de {name} ?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel
        )

        if answer == QMessageBox.StandardButton.Save:
            return editor.save()

        if answer == QMessageBox.StandardButton.Discard:
            return True

        return False

                                                           
                     
                                                           

    def new_file(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Créer un nouveau fichier",
            str(self.workspace / "nouveau.py"),
            "Python (*.py);;Tous les fichiers (*.*)"
        )

        if not path:
            return

        target = Path(path)

        if target.exists():
            QMessageBox.warning(
                self, "Attention",
                "Ce fichier existe déjà."
            )
            return

        try:
            target.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            target.write_text(
                "",
                encoding="utf-8"
            )

            self.add_editor(target)
            self.refresh_tree()

        except Exception as e:
            self.error(e)

    def open_file(self):

        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Ouvrir des fichiers",
            str(self.workspace),
            "Tous les fichiers (*.*)"
        )

        for path in paths:

            existing = self.find_tab(path)

            if existing >= 0:
                self.tabs.setCurrentIndex(existing)
            else:
                self.add_editor(path)

    def open_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Ouvrir un dossier",
            str(self.workspace)
        )

        if not folder:
            return

        self.workspace = Path(folder)

        self.model.setRootPath(folder)

        self.tree.setRootIndex(
            self.model.index(folder)
        )

        self.workspace_label.setText(folder)

        self.statusBar().showMessage(
            f"Dossier ouvert : {folder}"
        )

    def save_file(self):

        editor = self.editor()

        if editor is None:
            return

        if editor.path is None:
            self.save_as()
            return

        if editor.save():
            self.update_tab_title(editor)
            self.refresh_tree()
            self.statusBar().showMessage(
                "Fichier enregistré"
            )

    def save_as(self):

        editor = self.editor()

        if editor is None:
            return

        old_path = editor.path

        if not editor.save_as():
            return

        if old_path and old_path.resolve() != editor.path.resolve():
            existing = self.find_tab(editor.path)

            if existing >= 0 and self.tabs.widget(existing) is not editor:
                QMessageBox.warning(
                    self,
                    "Fichier déjà ouvert",
                    "Ce fichier est déjà ouvert dans un autre onglet."
                )
                editor.path = old_path
                return

        self.update_tab_title(editor)
        self.refresh_tree()

    def import_file(self):

        source, _ = QFileDialog.getOpenFileName(
            self,
            "Importer un fichier",
            str(Path.home())
        )

        if not source:
            return

        destination = QFileDialog.getExistingDirectory(
            self,
            "Choisir le dossier de destination",
            str(self.workspace)
        )

        if not destination:
            return

        target = Path(destination) / Path(source).name

        if target.exists():
            QMessageBox.warning(
                self, "Importation",
                "Un fichier portant ce nom existe déjà."
            )
            return

        try:
            shutil.copy2(source, target)
            self.refresh_tree()

            self.statusBar().showMessage(
                f"Importé : {target}"
            )

        except Exception as e:
            self.error(e)

    def export_file(self):

        editor = self.editor()

        if editor is None:
            return

        suggested = (
            editor.path.name
            if editor.path
            else "export.py"
        )

        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter une copie",
            str(Path.home() / suggested),
            "Tous les fichiers (*.*)"
        )

        if not destination:
            return

        try:
            Path(destination).write_text(
                editor.toPlainText(),
                encoding="utf-8"
            )

            self.statusBar().showMessage(
                f"Copie exportée : {destination}"
            )

        except Exception as e:
            self.error(e)

                                                           
               
                                                           

    def refresh_tree(self):

        self.model.setRootPath(
            str(self.workspace)
        )

        self.tree.setRootIndex(
            self.model.index(str(self.workspace))
        )

        self.tree.viewport().update()

    def selected_directory(self):

        index = self.tree.currentIndex()

        if index.isValid():

            path = Path(
                self.model.filePath(index)
            )

            if path.is_dir():
                return path

            return path.parent

        return self.workspace

    def tree_open(self, index):

        path = Path(
            self.model.filePath(index)
        )

        if path.is_file():

            existing = self.find_tab(path)

            if existing >= 0:
                self.tabs.setCurrentIndex(existing)
            else:
                self.add_editor(path)

    def new_folder(self):

        folder = self.selected_directory()

        name, ok = QInputDialog.getText(
            self,
            "Nouveau dossier",
            "Nom du dossier :"
        )

        if not ok or not name.strip():
            return

        target = folder / name.strip()

        try:
            target.mkdir(parents=False)
            self.refresh_tree()

        except Exception as e:
            self.error(e)

    def tree_context_menu(self, position):

        index = self.tree.indexAt(position)

        if not index.isValid():
            return

        path = Path(
            self.model.filePath(index)
        )

        menu = QMenu(self)

        open_action = menu.addAction("Ouvrir")
        rename_action = menu.addAction("Renommer")
        delete_action = menu.addAction("Supprimer")
        menu.addSeparator()

        copy_action = menu.addAction("Copier le chemin")

        selected = menu.exec(
            self.tree.viewport().mapToGlobal(position)
        )

        if selected == open_action:
            if path.is_file():
                self.tree_open(index)

        elif selected == rename_action:
            self.rename_path(path)

        elif selected == delete_action:
            self.delete_path(path)

        elif selected == copy_action:
            QApplication.clipboard().setText(
                str(path)
            )

    def rename_path(self, path):

        name, ok = QInputDialog.getText(
            self,
            "Renommer",
            "Nouveau nom :",
            text=path.name
        )

        if not ok or not name.strip():
            return

        destination = path.with_name(name.strip())

        if destination.exists():
            QMessageBox.warning(
                self, "Renommer",
                "Un élément portant ce nom existe déjà."
            )
            return

        try:
            path.rename(destination)

            index = self.find_tab(path)

            if index >= 0:
                editor = self.tabs.widget(index)
                editor.path = destination
                self.update_tab_title(editor)

            self.refresh_tree()

        except Exception as e:
            self.error(e)

    def delete_path(self, path):

        answer = QMessageBox.question(
            self,
            "Supprimer",
            f"Supprimer définitivement :\n{path} ?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:

            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

            for i in reversed(range(self.tabs.count())):
                editor = self.tabs.widget(i)

                if editor.path:
                    try:
                        if editor.path.resolve() == path.resolve():
                            self.tabs.removeTab(i)
                    except OSError:
                        pass

            self.refresh_tree()

        except Exception as e:
            self.error(e)

                                                           
            
                                                           

    def show_search(self):

        self.search_widget.show()
        self.search_input.setFocus()
        self.search_input.selectAll()

    def find_next(self):

        editor = self.editor()

        if editor is None:
            return

        text = self.search_input.text()

        if not text:
            return

        found = editor.find(text)

        if not found:
            cursor = editor.textCursor()
            cursor.movePosition(
                QTextCursor.MoveOperation.Start
            )
            editor.setTextCursor(cursor)

            if not editor.find(text):
                self.statusBar().showMessage(
                    "Aucun résultat"
                )

                                                           
               
                                                           

    def run_file(self):

        editor = self.editor()

        if editor is None:
            return

        if editor.path is None:
            if not editor.save_as():
                return

        elif editor.modified:
            if not editor.save():
                return

        path = editor.path

        if not path.exists():
            return

        commands = {
            ".py": [sys.executable, "-u", str(path)],
            ".js": ["node", str(path)],
            ".sh": ["bash", str(path)],
        }

        command = commands.get(path.suffix.lower())

        if not command:
            QMessageBox.warning(
                self,
                "Exécution",
                "Format non pris en charge."
            )
            return

        self.terminal.clear()
        self.terminal_dock.show()

        self.terminal.appendPlainText(
            f"> {' '.join(command)}\n"
        )

        if self.process is not None:
            if self.process.state() != QProcess.ProcessState.NotRunning:
                QMessageBox.warning(
                    self,
                    "Exécution",
                    "Un programme est déjà en cours."
                )
                return

        self.process = QProcess(self)

        self.process.setWorkingDirectory(
            str(path.parent)
        )

        self.process.setProcessChannelMode(
            QProcess.ProcessChannelMode.MergedChannels
        )

        self.process.readyReadStandardOutput.connect(
            self.read_process_output
        )

        self.process.finished.connect(
            self.process_finished
        )

        self.process.errorOccurred.connect(
            self.process_error
        )

        self.process.start(
            command[0],
            command[1:]
        )

    def read_process_output(self):

        if self.process is None:
            return

        data = self.process.readAllStandardOutput()

        self.terminal.moveCursor(
            QTextCursor.MoveOperation.End
        )

        self.terminal.insertPlainText(
            bytes(data).decode(
                "utf-8",
                errors="replace"
            )
        )

        self.terminal.moveCursor(
            QTextCursor.MoveOperation.End
        )

    def process_finished(self, code, status):

        self.read_process_output()

        self.terminal.appendPlainText(
            f"\n[Terminé : code {code}]"
        )

        self.statusBar().showMessage(
            f"Exécution terminée : code {code}"
        )

    def process_error(self, error):

        self.terminal.appendPlainText(
            f"\n[Erreur du processus : {error}]"
        )

    def stop_process(self):

        if self.process is None:
            return

        if self.process.state() != QProcess.ProcessState.NotRunning:

            self.process.terminate()

            if not self.process.waitForFinished(1500):
                self.process.kill()

            self.terminal.appendPlainText(
                "\n[Exécution arrêtée]"
            )

                                                           
          
                                                           

    def toggle_terminal(self):

        self.terminal_dock.setVisible(
            not self.terminal_dock.isVisible()
        )

    def toggle_explorer(self):

        self.splitter.widget(0).setVisible(
            not self.splitter.widget(0).isVisible()
        )

    def about(self):

        QMessageBox.about(
            self,
            "À propos de lupin Code",
            """
            <h2>lupin Code 2.0</h2>
            <p>Éditeur de code Python moderne.</p>
            <p>Interface native PySide6.</p>
            <p>Gestion locale des fichiers.</p>
            <p>Exécution et terminal intégrés.</p>
            <p>Conçu pour fonctionner hors ligne.</p>
            """
        )

                                                           
                
                                                           

    def close_tab(self, index):

        editor = self.tabs.widget(index)

        if not isinstance(editor, CodeEditor):
            return

        if not self.confirm_save(editor):
            return

        self.tabs.removeTab(index)
        editor.deleteLater()

    def closeEvent(self, event):

        for i in range(self.tabs.count()):

            editor = self.tabs.widget(i)

            if isinstance(editor, CodeEditor):

                if not self.confirm_save(editor):
                    event.ignore()
                    return

        self.stop_process()
        event.accept()

                                                           
            
                                                           

    def error(self, exception):

        QMessageBox.critical(
            self,
            "Erreur lupin Code",
            str(exception)
        )


                                                           
      
                                                           

def main():

    app = QApplication(sys.argv)

    app.setApplicationName("lupin Code")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)

    window = NexusCode()
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
