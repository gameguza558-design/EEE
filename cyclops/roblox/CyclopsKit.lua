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
		Kit.dress(character, outfitName, { shield = true?, stripAvatar = true?, accessories = { assetId, ... }? })
		  accessories: catalog accessories (e.g. hair you own) loaded by asset ID; an
		  accessory that replaces the hair also hides the outfit's own "Head_Hair" piece.
		  accessoryColor (Color3, optional): recolour them; outfits like the King have a
		  default hairTint so bought hair blends with the body.
		Kit.makeWeapon(weaponName) -> Tool   (weapons with dual = true also put a copy in the left hand)
		Kit.equip(character, weaponName) -> Tool    (NPCs hold it, players get it in the Backpack)
		Kit.spawnCreature(creatureName, cframe) -> clone of the rigged wolf, standing at cframe
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

	local hasAccessories = options.accessories ~= nil and #options.accessories > 0
	for _, template in folder:GetChildren() do
		local piece = info.pieces[template.Name]
		local partName, kind = string.match(template.Name, "^(%w+)_(%w+)$")
		if hasAccessories and (kind == "Hair" or kind == "HairOutline") then
			continue -- replaced by the loaded hair accessory
		end
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
		elseif string.match(kind, "Outline$") then
			-- Inverted-hull ink outline: black, relies on back-face culling.
			part.TextureID = ""
			part.Material = Enum.Material.SmoothPlastic
			part.Color = Color3.fromRGB(8, 6, 10)
			part.CastShadow = false
		elseif kind == "Body" then
			-- The painted R15 body replaces the original part's look.
			bodyPart.Transparency = 1
		end
		weld(bodyPart, part)
		part.Parent = holder
	end
	if hasAccessories then
		Kit.addAccessories(character, options.accessories, options.accessoryColor or info.hairTint)
	end
	return holder
end

-- Load catalog accessories (hair, etc.) by asset ID and put them on the character.
-- InsertService can load assets the game's creator owns or that Roblox allows.
-- Recolour a loaded accessory so it matches the outfit (e.g. the King's pink mane).
-- Works for MeshPart and SpecialMesh handles; a SurfaceAppearance (fixed PBR textures)
-- is removed because it cannot be recoloured.
function Kit.tintAccessory(accessory, color)
	for _, item in accessory:GetDescendants() do
		if item:IsA("SurfaceAppearance") then
			item:Destroy()
		elseif item:IsA("SpecialMesh") then
			item.TextureId = ""
			item.VertexColor = Vector3.new(color.R, color.G, color.B)
		elseif item:IsA("MeshPart") then
			item.TextureID = ""
		end
		if item:IsA("BasePart") then
			item.Color = color
			item.Material = Enum.Material.SmoothPlastic
		end
	end
end

function Kit.addAccessories(character, assetIds, tint)
	local InsertService = game:GetService("InsertService")
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	if not humanoid then
		return
	end
	for _, id in assetIds do
		local ok, result = pcall(InsertService.LoadAsset, InsertService, tonumber(id))
		if ok and result then
			local accessory = result:FindFirstChildWhichIsA("Accessory", true)
			if accessory then
				if tint then
					Kit.tintAccessory(accessory, tint)
				end
				humanoid:AddAccessory(accessory)
			end
			result:Destroy()
		else
			warn(`CyclopsKit: could not load accessory {id}: {result}`)
		end
	end
end

-------------------------------------------------------------------------------
-- Weapons

local function isCyclops(model)
	return model:FindFirstChild("CyclopsOutfit") ~= nil or model:GetAttribute("CyclopsCreature") ~= nil
end

-- Bleeding (saw-toothed weapons): damage over time; re-applying refreshes the timer.
-- While it lasts the humanoid has the attribute Bleeding = true, for status UI/effects.
Kit.BLEED_DAMAGE = 3 -- per tick
Kit.BLEED_TICK = 0.5 -- seconds
Kit.BLEED_DURATION = 4 -- seconds

function Kit.applyBleed(humanoid)
	humanoid:SetAttribute("BleedUntil", os.clock() + Kit.BLEED_DURATION)
	if humanoid:GetAttribute("Bleeding") then
		return -- already ticking; the new end time is picked up below
	end
	humanoid:SetAttribute("Bleeding", true)
	task.spawn(function()
		while humanoid.Parent and humanoid.Health > 0 and os.clock() < (humanoid:GetAttribute("BleedUntil") or 0) do
			task.wait(Kit.BLEED_TICK)
			humanoid:TakeDamage(Kit.BLEED_DAMAGE)
		end
		humanoid:SetAttribute("Bleeding", false)
	end)
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
		if info.bleed then
			Kit.applyBleed(humanoid)
		end
	end

	local function addParts(parts)
		for _, part in parts do
			if part:IsA("BasePart") then
				part.CanTouch = true
				part.Touched:Connect(onTouched)
			end
		end
	end
	addParts(tool:GetDescendants())

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
	return addParts
end

-- Builds a weapon's parts with the grip origin at `base`; returns the handle (the
-- other pieces are welded to it). Used for the Tool and for a dual wielder's off-hand copy.
local function buildWeaponParts(weaponName, base, parent)
	local info = Data.weapons[weaponName]
	local folder = asset("Weapons", weaponName)
	local handleInfo = info.pieces.Handle
	local handle = folder.Handle:Clone()
	prepare(handle, false)
	handle.Size = handleInfo.size
	handle.CFrame = base * CFrame.new(handleInfo.offset)
	handle.Parent = parent
	for _, template in folder:GetChildren() do
		local piece = info.pieces[template.Name]
		if template.Name == "Handle" or not piece or not template:IsA("BasePart") then
			continue
		end
		local part = template:Clone()
		prepare(part, true)
		part.Size = piece.size
		part.CFrame = base * CFrame.new(piece.offset)
		if string.match(template.Name, "Glow$") then
			glowify(part, info.glow, false)
		end
		weld(handle, part)
		part.Parent = parent
	end
	return handle
end

function Kit.makeWeapon(weaponName)
	local info = Data.weapons[weaponName]
	assert(info, `CyclopsKit: unknown weapon {weaponName}`)

	local tool = Instance.new("Tool")
	tool.Name = weaponName
	tool.CanBeDropped = false
	tool:SetAttribute("Damage", info.damage)
	tool:SetAttribute("TwoHanded", info.twoHanded)
	tool:SetAttribute("Dual", info.dual == true)

	local handleInfo = info.pieces.Handle
	local handle = buildWeaponParts(weaponName, CFrame.new(-handleInfo.offset), tool)
	handle.Name = "Handle"
	-- The model's origin is where the hand holds it.
	tool.Grip = CFrame.new(-handleInfo.offset) * info.grip
	local addParts = hookMelee(tool, info)

	if info.dual then
		-- Dual wielders: a second copy in the left hand while the tool is equipped. It
		-- swings with the main weapon (same damage, same Activated).
		local offhand
		tool.Equipped:Connect(function()
			local character = tool.Parent
			local hand = character and character:FindFirstChild("LeftHand")
			if not hand then
				return
			end
			local grip = hand:FindFirstChild("LeftGripAttachment")
			offhand = Instance.new("Model")
			offhand.Name = weaponName .. "Offhand"
			local base = hand.CFrame * (grip and grip.CFrame or CFrame.new(0, -hand.Size.Y / 2, 0)) * info.grip:Inverse()
			local h = buildWeaponParts(weaponName, base, offhand)
			h.Massless = true
			offhand.PrimaryPart = h
			offhand.Parent = character
			weld(hand, h)
			addParts(offhand:GetDescendants())
		end)
		tool.Unequipped:Connect(function()
			if offhand then
				offhand:Destroy()
				offhand = nil
			end
		end)
	end
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
	-- Wolves are skinned rigs (one MeshPart + Bones) imported from
	-- export/creatures/<Name>.fbx; the imported Model is cloned as-is.
	local model = asset("Creatures", creatureName):Clone()
	model:SetAttribute("CyclopsCreature", creatureName)
	if not model:FindFirstChildWhichIsA("Humanoid", true) and not model:FindFirstChildWhichIsA("AnimationController", true) then
		local controller = Instance.new("AnimationController")
		Instance.new("Animator").Parent = controller
		controller.Parent = model
	end
	for _, part in model:GetDescendants() do
		if part:IsA("BasePart") then
			part.Anchored = false
		end
	end
	if model.PrimaryPart == nil then
		model.PrimaryPart = model:FindFirstChildWhichIsA("BasePart", true)
	end
	local _, size = model:GetBoundingBox()
	model:PivotTo((cframe or CFrame.new()) * CFrame.new(0, size.Y / 2, 0))
	return model
end

return Kit
