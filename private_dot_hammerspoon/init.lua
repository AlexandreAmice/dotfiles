hs.autoLaunch(true)

-- Use familiar Ctrl shortcuts in GUI apps; terminals keep their native input.
local terminalApps = {
    ["com.mitchellh.ghostty"] = true,
    ["com.apple.Terminal"] = true,
    ["com.googlecode.iterm2"] = true,
    ["net.kovidgoyal.kitty"] = true,
    ["org.alacritty"] = true,
    ["com.github.wez.wezterm"] = true,
    ["dev.warp.Warp-Stable"] = true,
    ["co.zeit.hyper"] = true,
}
-- VS Code owns its Ctrl bindings so terminalFocus can preserve shell input.
local nativeShortcutApps = { ["com.microsoft.VSCode"] = true }
local commandKeys = {
    a = true, b = true, c = true, d = true, f = true, g = true,
    i = true, k = true, l = true, n = true, o = true, p = true,
    q = true, r = true, s = true, t = true, u = true, v = true,
    w = true, x = true, z = true,
    ["0"] = true, ["1"] = true, ["2"] = true, ["3"] = true,
    ["4"] = true, ["5"] = true, ["6"] = true, ["7"] = true,
    ["8"] = true, ["9"] = true, ["-"] = true, ["="] = true,
    ["/"] = true,
}
-- Common shifted actions: redo, reopen tab, new window, save as, find, etc.
local shiftedCommandKeys = {
    f = true, g = true, n = true, o = true, p = true, r = true,
    s = true, t = true, v = true, w = true, z = true, ["="] = true,
}
local navigationKeys = {
    left = {key = "left", modifier = "alt"},
    right = {key = "right", modifier = "alt"},
    delete = {key = "delete", modifier = "alt"},
    forwarddelete = {key = "forwarddelete", modifier = "alt"},
    home = {key = "up", modifier = "cmd"},
    ["end"] = {key = "down", modifier = "cmd"},
}
local heldShortcuts = {}
local shortcutEventTag = 0x4354524c
local keyEvent = hs.eventtap.event

local function sendShortcut(event, shortcut)
    if shortcut.native then
        -- Navigation has no AeroSpace conflict. Keep the physical event in
        -- the normal input stream so macOS can maintain hold-to-repeat.
        event:setKeyCode(shortcut.code):setFlags(shortcut.flags)
        return false
    end
    -- Posting to the app avoids AeroSpace intercepting Cmd+S/F/T/W and digits.
    event:copy():setKeyCode(shortcut.code):setFlags(shortcut.flags)
        :setProperty(keyEvent.properties.eventSourceUserData, shortcutEventTag)
        :post(shortcut.app)
    return true
end

appShortcuts = hs.eventtap.new({keyEvent.types.keyDown, keyEvent.types.keyUp}, function(event)
    if event:getProperty(keyEvent.properties.eventSourceUserData) == shortcutEventTag then
        return false
    end

    local code = event:getKeyCode()
    local held = heldShortcuts[code]
    if held then
        -- Keep repeats and key-up paired with the original mapping even if
        -- Ctrl is released first. Posted shortcuts also retain their app.
        if event:getType() == keyEvent.types.keyUp then
            heldShortcuts[code] = nil
        end
        return sendShortcut(event, held)
    end
    if event:getType() ~= keyEvent.types.keyDown then
        return false
    end

    local flags = event:getFlags()
    if not flags.ctrl or flags.cmd or flags.alt then
        return false
    end
    local key = hs.keycodes.map[code]
    local navigation = navigationKeys[key]
    if flags.fn and not navigation then
        return false
    end

    local app = hs.application.frontmostApplication()
    if not app or terminalApps[app:bundleID()] or nativeShortcutApps[app:bundleID()] then
        return false
    end

    local targetFlags = {shift = flags.shift or nil}
    local targetKey = key
    if navigation then
        targetKey = navigation.key
        targetFlags[navigation.modifier] = true
    elseif key == "y" and not flags.shift then
        targetKey = "z"
        targetFlags.cmd, targetFlags.shift = true, true
    elseif (flags.shift and shiftedCommandKeys[key]) or (not flags.shift and commandKeys[key]) then
        targetFlags.cmd = true
    else
        return false
    end

    local shortcut = {app = app, code = hs.keycodes.map[targetKey], flags = targetFlags,
        native = navigation ~= nil}
    heldShortcuts[code] = shortcut
    return sendShortcut(event, shortcut)
end):start()

-- Translate Ctrl+vertical scrolling into Ghostty's font-size shortcuts.
-- Ghostty does not provide a mouse-wheel keybind for this action.
local scroll = hs.eventtap.event
local properties = scroll.properties
local accumulated = 0
local lastDirection = 0
local lastEventTime = 0

ghosttyZoomOnScroll = hs.eventtap.new({scroll.types.scrollWheel}, function(event)
    local app = hs.application.frontmostApplication()
    if not app or app:bundleID() ~= "com.mitchellh.ghostty" or not event:getFlags().ctrl then
        return false
    end

    -- Trackpad momentum should not continue zooming after the gesture ends.
    if event:getProperty(properties.scrollWheelEventMomentumPhase) ~= 0 then
        return true
    end

    local continuous = event:getProperty(properties.scrollWheelEventIsContinuous) ~= 0
    local deltaProperty = continuous and properties.scrollWheelEventPointDeltaAxis1
        or properties.scrollWheelEventDeltaAxis1
    local delta = event:getProperty(deltaProperty)
    if delta == 0 then
        return true
    end

    local direction = delta > 0 and 1 or -1
    if continuous then
        local now = hs.timer.secondsSinceEpoch()
        if direction ~= lastDirection or now - lastEventTime > 0.4 then
            accumulated = 0
        end
        accumulated = accumulated + math.abs(delta)
        lastDirection = direction
        lastEventTime = now
        if accumulated < 40 then
            return true
        end
        accumulated = accumulated - 40
    end

    return true, scroll.newKeyEventSequence({"cmd"}, direction > 0 and "=" or "-")
end):start()
