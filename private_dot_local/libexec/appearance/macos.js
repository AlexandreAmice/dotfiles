ObjC.import('AppKit');
ObjC.import('Foundation');

function run(argv) {
    if (argv.length !== 2) throw new Error('Expected landscape and portrait wallpaper paths');
    const screens = $.NSScreen.screens;
    const workspace = $.NSWorkspace.sharedWorkspace;
    for (let i = 0; i < screens.count; i++) {
        const screen = screens.objectAtIndex(i);
        const size = screen.frame.size;
        const path = size.height > size.width ? argv[1] : argv[0];
        const url = $.NSURL.fileURLWithPath($(path));
        const error = Ref();
        if (!workspace.setDesktopImageURLForScreenOptionsError(url, screen, $({}), error)) {
            throw new Error('Cannot set wallpaper on screen ' + i + ': ' + ObjC.unwrap(error[0].localizedDescription));
        }
    }
}
