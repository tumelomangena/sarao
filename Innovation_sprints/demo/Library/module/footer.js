export function addFooterDiv(func) {
    const footerContent = "<h2>Footer Section</h2><p>This is the footer that was loaded dynamically.</p>";
    func('footerDiv', footerContent);
}
