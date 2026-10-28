package com.mohamedrejeb.calf.picker

import org.w3c.dom.HTMLInputElement
import org.w3c.files.File

internal actual class BrowserPickerDialogSpy actual constructor() {
    private val token = createPickerDialogSpy()
    actual val clickCount: Int get() = pickerClickCount(token)
    actual fun inputAt(index: Int): HTMLInputElement = pickerInputAt(token, index)
    actual fun select(input: HTMLInputElement, file: File) { pickerSelect(token, input, file) }
    actual fun close() { closePickerDialogSpy(token) }
}

private fun pickerClickCount(token: dynamic): Int = js("token.count()")
private fun pickerInputAt(token: dynamic, index: Int): HTMLInputElement = js("token.inputAt(index)")
private fun pickerSelect(token: dynamic, input: HTMLInputElement, file: File): Unit = js("{ token.select(input, file); }")
private fun closePickerDialogSpy(token: dynamic): Unit = js("{ token.close(); }")
private fun createPickerDialogSpy(): dynamic = js(
    """(function () {
        var proto = HTMLInputElement.prototype;
        var previous = Object.getOwnPropertyDescriptor(proto, 'click');
        var original = proto.click;
        var inputs = [];
        var closed = false;
        if (typeof original !== 'function' || typeof DataTransfer !== 'function') {
            throw new Error('Expected real browser input click and DataTransfer');
        }
        Object.defineProperty(proto, 'click', {
            configurable: true, writable: true,
            enumerable: previous ? previous.enumerable : false,
            value: function () {
                if (!(this instanceof HTMLInputElement) || this.type !== 'file' ||
                    this.name !== 'file' || this.style.display !== 'none') {
                    return original.apply(this, arguments);
                }
                if (this.parentNode !== document.body) throw new Error('Expected attached library input');
                inputs.push(this); // Only the OS chooser opening is intercepted.
            }
        });
        return {
            count: function () { return inputs.length; },
            inputAt: function (index) {
                if (!inputs[index]) throw new Error('Expected an actual captured picker input');
                return inputs[index];
            },
            select: function (input, file) {
                if (inputs.indexOf(input) < 0 || !(file instanceof File)) {
                    throw new Error('Expected captured input and real File');
                }
                var transfer = new DataTransfer();
                transfer.items.add(file);
                input.files = transfer.files;
                if (input.files.length !== 1 || input.files.item(0) !== file) {
                    throw new Error('Native FileList assignment failed');
                }
            },
            close: function () {
                if (closed) return;
                closed = true;
                if (previous) Object.defineProperty(proto, 'click', previous);
                else if (!delete proto.click) throw new Error('Could not restore input click');
                if (proto.click !== original) throw new Error('Input click restoration mismatch');
                var leaked = inputs.some(function (input) {
                    return input.parentNode !== null || input.onchange !== null || input.oncancel !== null;
                });
                inputs.forEach(function (input) {
                    input.onchange = null; input.oncancel = null; input.remove();
                });
                inputs = [];
                if (leaked) throw new Error('Production picker retained a DOM input/listener at teardown');
            }
        };
    })()""",
)
