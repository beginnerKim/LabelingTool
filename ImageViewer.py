from PySide2.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PySide2.QtGui import QPixmap, QImage
from PySide2.QtGui import QMouseEvent, QResizeEvent
from PySide2.QtCore import Qt, QPoint, QRect

import numpy as np
from typing import Optional

class ImageViewer(QWidget):
    @staticmethod
    def parsingImageFormat(__image:np.ndarray) -> QImage.Format:
        if __image is None: return QImage.Format.Format_Invalid

        if len(__image.shape) == 2:
            return QImage.Format.Format_Grayscale8
        elif len(__image.shape) == 3:
            if __image.shape[2] == 1:
                return QImage.Format.Format_Grayscale8
            elif __image.shape[2] == 3:
                return QImage.Format.Format_RGB888
            elif __image.shape[2] == 4:
                return QImage.Format.Format_ARGB32

        raise ValueError


    def __init__(self, parent:Optional[QWidget] = None):
        super().__init__(parent)

        # params
        self.__fitSize:bool = False # image를 widget size에 맞게 출력


        self.__srcPixmap:Optional[QPixmap] = None
        self.__displayOffset = QPoint(0, 0) # offset from image center (pixel)
        self.__zoomScale:float = 1.

        ## for mouse control
        self.__mouseButtonMask:int = Qt.MouseButton.NoButton
        self.__mouseMoveLastPoint = QPoint(0, 0)



        self.__displayPannel = QLabel()
        self.__displayPannel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.__displayPannel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.__displayPannel.mousePressEvent = self.__displayPannelMousePressEvent # override event
        self.__displayPannel.mouseReleaseEvent = self.__displayPannelMouseReleaseEvent
        self.__displayPannel.mouseMoveEvent = self.__displayPannelMouseMoveEvent



        layout = QVBoxLayout()
        layout.addWidget(self.__displayPannel)
        self.setLayout(layout)

    def __displayPannelMousePressEvent(self, event:QMouseEvent):
        if self.__mouseButtonMask == Qt.MouseButton.NoButton: # 하나의 버튼 입력만 처리한다.
            self.__mousePressStartPoint = event.pos()
            self.__mouseMoveLastPoint = event.pos()
            self.__mouseButtonMask |= event.button()

    def __displayPannelMouseReleaseEvent(self, event:QMouseEvent):
        self.__mouseButtonMask = Qt.MouseButton.NoButton

    def __displayPannelMouseMoveEvent(self, event:QMouseEvent):
        if self.__mouseButtonMask & Qt.MouseButton.RightButton > 0:
            self.__displayOffset += self.__mouseMoveLastPoint - event.pos()
            self.__mouseMoveLastPoint = event.pos()
            self.__updateImage()

    def reset(self):
        self.__displayPannel.clear()

        self.__fitSize = False
        
        self.__srcPixmap = None
        self.__displayOffset = QPoint(0, 0)
        self.__zoomScale = 1.

        self.__mouseButtonMask = Qt.MouseButton.NoButton
        self.__mousePressStartPoint = QPoint(0, 0)
        self.__mouseMoveLastPoint = QPoint(0, 0)




    def setImage(self, image:np.ndarray, fitSize:bool = False):
        self.reset()
        self.__fitSize = fitSize

        qimage = QImage(image, image.shape[1], image.shape[0], image.strides[0], self.parsingImageFormat(image))
        self.__srcPixmap = QPixmap.fromImage(qimage)

        self.__updateImage()

    def __updateImage(self):
        if self.__srcPixmap is None: return

        if self.__fitSize:
            scaledPixmap = self.__srcPixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        else:
            scaledPixmap = self.__srcPixmap.scaled(self.size() * self.__zoomScale, Qt.AspectRatioMode.KeepAspectRatio)

        # crop for display
        cropRect = self.rect() # init rect by widget size
        cropRect.moveCenter(scaledPixmap.rect().center() + self.__displayOffset) # move crop rect to center of image (with offset)

        ## adjust range
        if cropRect.left() < 0: cropRect.moveLeft(0)
        if cropRect.top() < 0: cropRect.moveTop(0)
        if cropRect.right() > scaledPixmap.rect().right(): cropRect.moveRight(scaledPixmap.rect().right()-1)
        if cropRect.bottom() > scaledPixmap.rect().bottom(): cropRect.moveBottom(scaledPixmap.rect().bottom())

        self.__displayOffset = cropRect.center() - scaledPixmap.rect().center()# re-calculate offset by adjsted crop range

        ## do crop
        image = scaledPixmap.copy(cropRect)

        # set cropped pixmap to label
        self.__displayPannel.setPixmap(image)


    def resizeEvent(self, event: QResizeEvent) -> None:
        self.__updateImage()


# for test code
if __name__ == "__main__":
    from PySide2.QtWidgets import QApplication, QMainWindow
    app = QApplication()
    window = QMainWindow()
    widget = ImageViewer()
    window.setCentralWidget(widget)
    window.show()

    import cv2
    image = cv2.imread("D:\\Backups\\images\\Panel\\01. X2678_Bottom_Cam1\\Brightness\\Brightness_01-13-04_Cam1_OK.png", cv2.IMREAD_COLOR)
    widget.setImage(image, True)
    app.exec_()