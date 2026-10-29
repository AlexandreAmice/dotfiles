-- Compile as an application to expose it in the macOS app launcher:
-- osacompile -o "/Applications/Chrome New Window.app" scripts/chrome-new-window.applescript
on run
    do shell script "/usr/bin/open -na 'Google Chrome' --args --new-window about:blank"
end run
