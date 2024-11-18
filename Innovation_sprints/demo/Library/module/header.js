export function addHeaderDiv(func) {
    const headerContent = "<h2>Header Section</h2><p>This is the header that was loaded dynamically.</p>";
    func('headerDiv', headerContent);
}
