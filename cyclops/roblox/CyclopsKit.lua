--[[
	CyclopsKit (ModuleScript, put it in ServerScriptService)

	Dresses R15 rigs in cyclops outfits, builds weapon Tools and assembles jointed
	wolves, using the meshes imported from cyclops/export and the generated
	CyclopsData module.

	Expected layout:
		ReplicatedStorage
		├─ CyclopsData (ModuleScript)         <- roblox/CyclopsData.lua
		└─ CyclopsAssets (Folder)
		   ├─ Outfits/<OutfitName>/...        <- MeshParts from export/outfits/<OutfitName>.fbx
		   ├─ Weapons/<WeaponName>/...        <- MeshParts from export/weapons/<WeaponName>.fbx
		   └─ Creatures/<CreatureName>/...    <- MeshParts from export/creatures/<CreatureName>.fbx

	API:
		Kit.dress(character, outfitName, { shield = true?, stripAvatar = true? })
		Kit.makeWeapon(weaponName) -> Tool
		Kit.equip(character, weaponName) -> Tool    (NPCs hold it, players get it in the Backpack)
		Kit.spawnCreature(creatureName, cframe) -> Model with Humanoid + Motor6Ds
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Data = require(ReplicatedStorage:WaitForChild("CyclopsData"))
local Assets = ReplicatedStorage:WaitForChild("CyclopsAssets")

local Kit = {}

-- Set true if every imported mesh shows up facing backwards.
Kit.FLIP_180 = false
Kit.BODY_COLOR = Color3.fromRGB(28, 27, 31)

local function asset(kind, name)
	local folder = Assets:FindFirstChild(kind)
	local found = folder and folder:FindFirstChild(name)
	assert(found, `CyclopsKit: missing ReplicatedStorage.CyclopsAssets.{kind}.{name}`)
	return found
end

local function flip()
	return Kit.FLIP_180 and CFrame.Angles(0, math.pi, 0) or CFrame.identity
end

local function prepare(part, massless)
	part.Anchored = false
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.Massless = massless
end

local function glowify(part, color, withLight)
	part.TextureID = ""
	part.Material = Enum.Material.Neon
	part.Color = color
	if withLight then
		local light = Instance.new("PointLight")
		light.Color = color
		light.Brightness = 1.5
		light.Range = 8
		light.Parent = part
	end
end

local function weld(a, b)
	local w = Instance.new("WeldConstraint")
	w.Part0 = a
	w.Part1 = b
	w.Parent = b
end

-------------------------------------------------------------------------------
-- Outfits

local function stripAvatar(character)
	for _, item in character:GetChildren() do
		if item:IsA("Accessory") or item:IsA("Clothing") or item:IsA("ShirtGraphic") or item:IsA("BodyColors") then
			item:Destroy()
		end
	end
	local head = character:FindFirstChild("Head")
	local face = head and head:FindFirstChildOfClass("Decal")
	if face then
		face:Destroy()
	end
	for name in Data.blockSize do
		local part = character:FindFirstChild(name)
		if part and part:IsA("BasePart") then
			part.Color = Kit.BODY_COLOR
		end
	end
end

function Kit.dress(character, outfitName, options)
	options = options or {}
	local info = Data.outfits[outfitName]
	assert(info, `CyclopsKit: unknown outfit {outfitName}`)
	local folder = asset("Outfits", outfitName)
	local torso = character:FindFirstChild("UpperTorso")
	assert(torso, "CyclopsKit: dress() needs an R15 character")

	local old = character:FindFirstChild("CyclopsOutfit")
	if old then
		old:Destroy()
	end
	if options.stripAvatar ~= false then
		stripAvatar(character)
	end

	local holder = Instance.new("Folder")
	holder.Name = "CyclopsOutfit"
	holder:SetAttribute("Outfit", outfitName)
	holder.Parent = character
	-- The head is scaled with the torso height; other parts stretch per axis to fit.
	local uniform = torso.Size.Y / Data.blockSize.UpperTorso.Y

	for _, template in folder:GetChildren() do
		local piece = info.pieces[template.Name]
		local partName, kind = string.match(template.Name, "^(%w+)_(%w+)$")
		local bodyPart = partName and character:FindFirstChild(partName)
		if not (piece and bodyPart and template:IsA("BasePart")) then
			continue
		end
		if string.find(kind, "^Shield") and not options.shield then
			continue
		end
		local scale = if partName == "Head" then Vector3.one * uniform else bodyPart.Size / Data.blockSize[partName]

		local part = template:Clone()
		prepare(part, true)
		-- Setting Size also corrects any unit mismatch from the import.
		part.Size = piece.size * scale
		part.CFrame = bodyPart.CFrame * flip() * CFrame.new(piece.offset * scale)
		if string.match(kind, "Glow$") then
			glowify(part, info.glow, partName == "Head" or partName == "UpperTorso")
		end
		weld(bodyPart, part)
		part.Parent = holder
	end
	return holder
end

-------------------------------------------------------------------------------
-- Weapons

local function isCyclops(model)
	return model:FindFirstChild("CyclopsOutfit") ~= nil or model:GetAttribute("CyclopsCreature") ~= nil
end

local function hookMelee(tool, info)
	local canSwing, swinging, hit = true, false, {}
	local slash = Instance.new("Sound")
	slash.SoundId = "rbxasset://sounds/swordslash.wav"
	slash.Volume = 0.7
	slash.Parent = tool.Handle

	local function owner()
		local model = tool.Parent
		return model, model and model:FindFirstChildOfClass("Humanoid")
	end

	local function onTouched(other)
		if not swinging then
			return
		end
		local me = owner()
		local target = other:FindFirstAncestorOfClass("Model")
		if not target or target == me then
			return
		end
		local humanoid = target:FindFirstChildOfClass("Humanoid")
		if not humanoid or humanoid.Health <= 0 or hit[humanoid] then
			return
		end
		if isCyclops(me) and isCyclops(target) then
			return -- the corrupted don't hurt each other
		end
		local p1, p2 = Players:GetPlayerFromCharacter(me), Players:GetPlayerFromCharacter(target)
		if p1 and p2 and not p1.Neutral and p1.Team == p2.Team then
			return
		end
		hit[humanoid] = true
		humanoid:TakeDamage(info.damage)
	end

	for _, part in tool:GetDescendants() do
		if part:IsA("BasePart") then
			part.CanTouch = true
			part.Touched:Connect(onTouched)
		end
	end

	-- Players trigger this by clicking; NPC scripts call tool:Activate().
	tool.Activated:Connect(function()
		local _, humanoid = owner()
		if not canSwing or not humanoid or humanoid.Health <= 0 then
			return
		end
		canSwing, swinging = false, true
		table.clear(hit)
		local anim = Instance.new("StringValue")
		anim.Name = "toolanim"
		anim.Value = "Slash"
		anim.Parent = tool
		slash:Play()
		task.wait(math.min(0.45, info.cooldown * 0.6))
		swinging = false
		task.wait(info.cooldown * 0.4)
		canSwing = true
	end)
end

function Kit.makeWeapon(weaponName)
	local info = Data.weapons[weaponName]
	assert(info, `CyclopsKit: unknown weapon {weaponName}`)
	local folder = asset("Weapons", weaponName)

	local tool = Instance.new("Tool")
	tool.Name = weaponName
	tool.CanBeDropped = false
	tool:SetAttribute("Damage", info.damage)
	tool:SetAttribute("TwoHanded", info.twoHanded)

	local handleInfo = info.pieces.Handle
	local handle = folder.Handle:Clone()
	prepare(handle, false)
	handle.Size = handleInfo.size
	handle.CFrame = CFrame.new()
	handle.Parent = tool
	for _, template in folder:GetChildren() do
		local piece = info.pieces[template.Name]
		if template.Name == "Handle" or not piece or not template:IsA("BasePart") then
			continue
		end
		local part = template:Clone()
		prepare(part, true)
		part.Size = piece.size
		part.CFrame = handle.CFrame * CFrame.new(piece.offset - handleInfo.offset)
		if string.match(template.Name, "Glow$") then
			glowify(part, info.glow, false)
		end
		weld(handle, part)
		part.Parent = tool
	end
	-- The model's origin is where the hand holds it.
	tool.Grip = CFrame.new(-handleInfo.offset) * info.grip
	hookMelee(tool, info)
	return tool
end

function Kit.equip(character, weaponName)
	local tool = Kit.makeWeapon(weaponName)
	local player = Players:GetPlayerFromCharacter(character)
	if player then
		tool.Parent = player:WaitForChild("Backpack")
	else
		local humanoid = character:FindFirstChildOfClass("Humanoid")
		tool.Parent = character
		if humanoid then
			humanoid:EquipTool(tool)
		end
	end
	return tool
end

-------------------------------------------------------------------------------
-- Creatures

function Kit.spawnCreature(creatureName, cframe)
	local info = Data.creatures[creatureName]
	assert(info, `CyclopsKit: unknown creature {creatureName}`)
	local folder = asset("Creatures", creatureName)
	cframe = cframe or CFrame.new()

	local model = Instance.new("Model")
	model.Name = creatureName
	model:SetAttribute("CyclopsCreature", creatureName)
	local parts = {}
	for name, piece in info.parts do
		local part = folder[name]:Clone()
		part.Anchored = false
		part.CanCollide = false
		part.Size = piece.size
		part.CFrame = cframe * flip() * CFrame.new(piece.offset)
		part.Parent = model
		parts[name] = part
	end

	local torso = parts[info.root]
	local root = Instance.new("Part")
	root.Name = "HumanoidRootPart"
	root.Size = torso.Size
	root.CFrame = torso.CFrame
	root.Transparency = 1
	root.CanCollide = true
	root.Parent = model
	model.PrimaryPart = root

	local function motor(name, part0, part1, pivot)
		local m = Instance.new("Motor6D")
		m.Name = name
		m.Part0 = part0
		m.Part1 = part1
		m.C0 = part0.CFrame:ToObjectSpace(pivot)
		m.C1 = part1.CFrame:ToObjectSpace(pivot)
		m.Parent = part0
	end
	motor("RootJoint", root, torso, torso.CFrame)
	for name, piece in info.parts do
		if piece.parent then
			motor(name .. "Joint", parts[piece.parent], parts[name], cframe * flip() * CFrame.new(piece.pivot))
		end
	end

	local humanoid = Instance.new("Humanoid")
	humanoid.HipHeight = root.Position.Y - cframe.Position.Y - root.Size.Y / 2
	humanoid.Parent = model
	return model
end

return Kit
