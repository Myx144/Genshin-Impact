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
        color: control.enabled ? "#e5eeff" : "#7383a1"
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        implicitWidth: 88
        implicitHeight: 36
        radius: 7
        color: !control.enabled
            ? "#202b3e"
            : (control.down
                ? "#142238"
                : (control.hovered ? "#243a5d" : "#1a2943"))
        border.width: 1
        border.color: !control.enabled
            ? "#2c3950"
            : (control.hovered ? "#5f7fab" : "#3d567d")
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
