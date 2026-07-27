import QtQuick
import QtQuick.Controls

CheckBox {
    id: control
    hoverEnabled: true
    focusPolicy: Qt.NoFocus

    MouseArea {
        anchors.fill: parent
        z: 1000
        enabled: control.enabled
        acceptedButtons: Qt.NoButton
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
    }
}

