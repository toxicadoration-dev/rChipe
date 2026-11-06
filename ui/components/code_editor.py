import re

from core.qt_compat import QtWidgets, QtGui, Signal, Qt, QRect, QSize


class JsonSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.active = True
        self.key_format = self._format("#9cdcfe")
        self.string_format = self._format("#ce9178")
        self.number_format = self._format("#b5cea8")
        self.keyword_format = self._format("#569cd6")
        self.string_pattern = re.compile(r'"(?:[^"\\]|\\.)*"')
        self.number_pattern = re.compile(r"-?(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+\b)?")
        self.keyword_pattern = re.compile(r"\b(?:true|false|null)\b")

    def _format(self, color):
        text_format = QtGui.QTextCharFormat()
        text_format.setForeground(QtGui.QColor(color))
        return text_format

    def highlightBlock(self, text):
        if not self.active:
            return

        string_ranges = []
        for match in self.string_pattern.finditer(text):
            string_ranges.append((match.start(), match.end()))
            end = match.end()
            while end < len(text) and text[end].isspace():
                end += 1
            text_format = self.key_format if end < len(text) and text[end] == ":" else self.string_format
            self.setFormat(match.start(), match.end() - match.start(), text_format)

        for pattern, text_format in (
            (self.number_pattern, self.number_format),
            (self.keyword_pattern, self.keyword_format),
        ):
            for match in pattern.finditer(text):
                if any(start <= match.start() < end for start, end in string_ranges):
                    continue
                self.setFormat(match.start(), match.end() - match.start(), text_format)


class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class HttpCodeEditor(QtWidgets.QPlainTextEdit):
    send_requested = Signal()

    def __init__(self, parent=None, read_only=False):
        super().__init__(parent)
        self.setReadOnly(read_only)
        self.line_number_area = LineNumberArea(self)

        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(11)
        self.setFont(font)

        font_metrics = QtGui.QFontMetrics(font)
        self.setTabStopDistance(4 * font_metrics.horizontalAdvance(' '))

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

        self.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event):
        painter = QtGui.QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QtGui.QColor("#131418"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        painter.setPen(QtGui.QColor("#4b5563"))
        font = self.font()
        font.setPointSize(10)
        painter.setFont(font)

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()
            line_color = QtGui.QColor("#1a1c26")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QtGui.QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if (
            event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.send_requested.emit()
            return
        super().keyPressEvent(event)
