-- Run from the repository root with: luajit tests/validate-hammerspoon.lua
-- Exercise routing without posting keys to real apps or touching the clipboard.
local callback
local frontApp
local posted = {}
local codes = {}
for i, key in ipairs({
    "a", "b", "c", "d", "f", "g", "h", "i", "k", "l", "n", "o", "p",
    "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2",
    "3", "4", "5", "6", "7", "8", "9", "-", "=", "/", "left", "right",
    "delete", "forwarddelete", "home", "end", "up", "down", "tab",
}) do
    codes[key], codes[i] = i, key
end
local function copy(source)
    local result = {}
    for key, value in pairs(source) do result[key] = value end
    return result
end
local function app(id)
    return {bundleID = function() return id end}
end
local gui = app("com.apple.TextEdit")
frontApp = gui
hs = {
    autoLaunch = function() end,
    application = {frontmostApplication = function() return frontApp end},
    keycodes = {map = codes},
    eventtap = {
        event = {types = {keyDown = 10, keyUp = 11, scrollWheel = 22},
            properties = {eventSourceUserData = 42, keyboardEventAutorepeat = 43}},
        new = function(types, fn)
            if types[1] == 10 then callback = fn end
            return {start = function(self) return self end}
        end,
    },
}
local function event(key, flags, kind)
    local e = {code = codes[key], flags = copy(flags), kind = kind or 10, properties = {}}
    function e:getKeyCode() return self.code end
    function e:getFlags() return copy(self.flags) end
    function e:getType() return self.kind end
    function e:getProperty(property) return self.properties[property] or 0 end
    function e:setKeyCode(code) self.code = code; return self end
    function e:setFlags(mods) self.flags = copy(mods); return self end
    function e:setProperty(property, value) self.properties[property] = value; return self end
    function e:copy()
        local cloned = event(codes[self.code], self.flags, self.kind)
        cloned.properties = copy(self.properties)
        return cloned
    end
    function e:post(target)
        assert(target, "shortcut must be sent directly to an app, not globally")
        posted[#posted + 1] = {app = target, event = self}
        assert(callback(self) == false, "synthetic event must not be remapped again")
        return self
    end
    return e
end
assert(loadfile("private_dot_hammerspoon/init.lua"))()
local function chord(key, flags, targetKey, targetFlags, native)
    posted = {}
    local down = event(key, flags)
    assert(callback(down) == not native)
    -- Users can release Ctrl before the letter; key-up must still match.
    local up = event(key, {}, 11)
    assert(callback(up) == not native)
    local delivered = posted
    if native then
        assert(#posted == 0, "navigation must keep native repeat, without posting replacement events")
        delivered = {{app = frontApp, event = down}, {app = frontApp, event = up}}
    end
    assert(#delivered == 2)
    for i, entry in ipairs(delivered) do
        assert(entry.app == frontApp)
        assert(entry.event.code == codes[targetKey])
        assert(entry.event.kind == (i == 1 and 10 or 11))
        for _, mod in ipairs({"ctrl", "cmd", "alt", "shift", "fn"}) do
            assert(not not entry.event.flags[mod] == not not targetFlags[mod], key .. ": " .. mod)
        end
    end
end
for key in ("a b c d f g i k l n o p q r s t u v w x z 0 1 2 3 4 5 6 7 8 9 - = /"):gmatch("%S+") do
    chord(key, {ctrl = true}, key, {cmd = true})
end
chord("y", {ctrl = true}, "z", {cmd = true, shift = true})
for key in ("f g n o p r s t v w z ="):gmatch("%S+") do
    chord(key, {ctrl = true, shift = true}, key, {cmd = true, shift = true})
end
for _, shifted in ipairs({false, true}) do
    for _, key in ipairs({"left", "right", "delete", "forwarddelete"}) do
        chord(key, {ctrl = true, shift = shifted, fn = true}, key, {alt = true, shift = shifted}, true)
    end
    chord("home", {ctrl = true, shift = shifted}, "up", {cmd = true, shift = shifted}, true)
    chord("end", {ctrl = true, shift = shifted}, "down", {cmd = true, shift = shifted}, true)
end
local function unchanged(key, flags)
    posted = {}
    assert(callback(event(key, flags)) == false)
    assert(callback(event(key, {}, 11)) == false)
    assert(#posted == 0)
end
for _, flags in ipairs({{}, {cmd = true}, {ctrl = true, cmd = true},
    {ctrl = true, alt = true}, {ctrl = true, fn = true}}) do
    unchanged("s", flags)
end
unchanged("h", {ctrl = true})
unchanged("tab", {ctrl = true})
unchanged("a", {ctrl = true, shift = true})
for _, id in ipairs({"com.mitchellh.ghostty", "com.apple.Terminal", "com.googlecode.iterm2",
    "net.kovidgoyal.kitty", "org.alacritty", "com.github.wez.wezterm", "dev.warp.Warp-Stable", "co.zeit.hyper", "com.microsoft.VSCode"}) do
    frontApp = app(id)
    for _, key in ipairs({"a", "c", "v", "x", "z", "y", "s", "left", "delete"}) do
        unchanged(key, {ctrl = true})
    end
end
frontApp = nil
unchanged("c", {ctrl = true})
frontApp = gui
posted = {}
-- Repeated physical Backspace events must propagate, retaining repeat flags.
for i = 0, 4 do
    local e = event("delete", {ctrl = true})
        :setProperty(hs.eventtap.event.properties.keyboardEventAutorepeat, i == 0 and 0 or 1)
    assert(callback(e) == false)
    assert(e.flags.alt and not e.flags.ctrl)
    assert(e:getProperty(hs.eventtap.event.properties.keyboardEventAutorepeat) == (i == 0 and 0 or 1))
    assert(#posted == 0)
end
assert(callback(event("delete", {}, 11)) == false)
unchanged("delete", {})
posted = {}
assert(callback(event("t", {ctrl = true})))
frontApp = app("com.apple.Terminal")
assert(callback(event("t", {ctrl = true}))) -- repeat after focus change
assert(callback(event("t", {}, 11)))
assert(#posted == 3)
for _, entry in ipairs(posted) do assert(entry.app == gui) end
unchanged("t", {ctrl = true}) -- key-up cleared the previous route
print("Hammerspoon shortcut routing passed: mappings, modifiers, terminal exclusions, repeats, key-up, and app targeting")
