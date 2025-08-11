/** @odoo-module **/

import { onMounted, useState, onPatched } from "@odoo/owl";
import { BinaryField } from "@web/views/fields/binary/binary_field";
import { registry } from "@web/core/registry";
var file_mimeType = "";
export class BinaryPreviewer extends BinaryField {
    setup() {
        super.setup();
        this.fileMimeType = useState({
            value: ""
        });
        this.image_src = useState({
            value: ""
        });
        async function getMimeTypeFromURL(url) {
            await fetch(url)
                .then(response => {
                    if (response.ok) {
                        return response.blob();
                    } else {
                        throw new Error('Failed to fetch the file');
                    }
                })
                .then(blob => {
                    const type = blob.type;
                    //                    console.log('MIME Type:', type);
                    file_mimeType = type;
                })
                .catch(error => {
                    //                    console.error('Error:', error);
                });
        }
        onMounted(async () => {
            var res_model = this.props.record.resModel;
            var res_id = this.props.record.resId ? this.props.record.resId : this.props.record.data.id;
            var url = '/web/content/' + res_model + '/' + res_id + '/' + this.props.name;
            if (this.props.record.resId || this.props.record.data.id) {
                fetch(url, {
                    cache: 'reload',
                });
                await getMimeTypeFromURL(url);
                if (file_mimeType.includes('image')) {
                    if (this.props.record.resId) {
                        var image = document.getElementById('img_' + this.props.name + '_' + this.props.record.resId);
                        if (image) {
                            image.src = url;
                            image.style.display = "inline";
                            //                        console.log('image src', image.src);
                            var viewer = new Viewer(image);
                        }
                    }
                    else {
                        var image = document.getElementById('img_' + this.props.name + '_' + this.props.record.data.id);
                        if (image) {
                            image.src = url;
                            image.style.display = "inline";
                            //                        console.log('image src', image.src);
                            var viewer = new Viewer(image);
                        }
                    }
                }
                else {
                    if (this.props.record.resId) {
                        var button = document.getElementById('btn_' + this.props.name + '_' + this.props.record.resId);
                        if (button) {
                            button.style.display = "inline";
                        }
                    }
                    else {
                        var button = document.getElementById('btn_' + this.props.name + '_' + this.props.record.data.id);
                        if (button) {
                            button.style.display = "inline";
                        }
                    }

                }
            }
        });

        onPatched(async () => {
            var res_model = this.props.record.resModel;
            var res_id = this.props.record.resId ? this.props.record.resId : this.props.record.data.id;
            var url = '/web/content/' + res_model + '/' + res_id + '/' + this.props.name;
            if (this.props.record.resId || this.props.record.data.id) {
                fetch(url, {
                    cache: 'reload',
                });
                await getMimeTypeFromURL(url);
                if (file_mimeType.includes('image') && this.props.name != "undefined") {
                    var image = document.getElementById('img_' + this.props.name + '_' + this.props.record.resId);
                    var button = document.getElementById('btn_' + this.props.name + '_' + this.props.record.resId);
                    if (this.props.record.resId) {
                        if (image) {
                            image.src = url;
                            image.style.display = "inline";
                            button.style.display = "none";
                            //                        console.log('image src', image.src);
                            var viewer = new Viewer(image);
                        }
                    }
                    else {
                        var image = document.getElementById('img_' + this.props.name + '_' + this.props.record.data.id);
                        var button = document.getElementById('btn_' + this.props.name + '_' + this.props.record.data.id);
                        if (image) {
                            image.src = url;
                            image.style.display = "inline";
                            button.style.display = "none";
                            //                        console.log('image src', image.src);
                            var viewer = new Viewer(image);
                        }
                    }
                }
                else {
                    var image = document.getElementById('img_' + this.props.name + '_' + this.props.record.resId);
                    var button = document.getElementById('btn_' + this.props.name + '_' + this.props.record.resId);
                    if (this.props.name != "undefined") {
                        console.log('url else', url);
                        if (this.props.record.resId) {
                            var button = document.getElementById('btn_' + this.props.name + '_' + this.props.record.resId);
                            if (button) {
                                button.style.display = "inline";
                                image.style.display = "none";
                            }
                        }
                        else {
                            var image = document.getElementById('img_' + this.props.name + '_' + this.props.record.data.id);
                            var button = document.getElementById('btn_' + this.props.name + '_' + this.props.record.data.id);
                            if (button) {
                                button.style.display = "inline";
                                image.style.display = "none";
                            }
                        }
                    }
                }
            }
        });
    }
    onclick_pdf_preview(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var res_model = this.props.record.resModel;
        var res_id = this.props.record.resId ? this.props.record.resId : this.props.record.data.id;
        var url = '/web/content/' + res_model + '/' + res_id + '/' + this.props.name;
        window.open(url, '_blank');
    };
    onclick_img_preview(ev) {
        ev.preventDefault();
        ev.stopPropagation();
    };
    onclick_download(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var res_model = this.props.record.resModel;
        var res_id = this.props.record.resId ? this.props.record.resId : this.props.record.data.id;
        var url = '/web/content/' + res_model + '/' + res_id + '/' + this.props.name + '?download=true';
        window.open(url, '_blank');
    };

}
BinaryPreviewer.template = "nthub_preview_image";
export default BinaryPreviewer
registry.category('fields').add("nt_binary_preview", BinaryPreviewer);





