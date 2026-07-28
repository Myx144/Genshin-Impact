import QtQuick
import QtQuick.Controls

AbstractButton {
    id: control
    hoverEnabled: true
    focusPolicy: Qt.NoFocus

    implicitWidth: Math.max(
        background ? background.implicitWidth : 0,
        contentItem ? contentItem.implicitWidth + leftPadding + rightPadding : 0
    )
    implicitHeight: Math.max(
        background ? background.implicitHeight : 0,
        contentItem ? contentItem.implicitHeight + topPadding + bottomPadding : 0
    )

    contentItem: Text {
        text: control.text
        font: control.font
        color: control.enabled ? "#181817" : "#85857f"
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        implicitWidth: 88
        implicitHeight: 36
        radius: 2
        color: !control.enabled
            ? "#fafafa"
            : (control.down
                ? "#f4f4f4"
                : (control.hovered ? "#f8f8f8" : "#ffffff"))
        border.width: 1
        border.color: !control.enabled
            ? "#d2d2cd"
            : (control.hovered ? "#8a8a84" : "#bdbdb7")
        Behavior on color { ColorAnimation { duration: 110 } }
        Behavior on border.color { ColorAnimation { duration: 110 } }
    }

    MouseArea {
        anchors.fill: parent
        z: 1000
        enabled: control.enabled
        acceptedButtons: Qt.NoButton
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
    }
}
