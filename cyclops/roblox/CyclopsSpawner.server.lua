--[[
	CyclopsSpawner (Script, put it in ServerScriptService next to CyclopsKit)

	Dresses NPCs placed in Workspace by attributes, so level design needs no code:

		R15 rig (e.g. from Avatar > Rig Builder > R15 Block Rig)
			Attribute CyclopsOutfit  (string)  e.g. "KnightMid"
			Attribute CyclopsWeapon  (string)  e.g. "MidSword"      (optional)
			Attribute CyclopsShield  (bool)    true for sword + shield (knights only)
			Attribute CyclopsAccessories (string) asset IDs, e.g. "1234567,7654321" - hair you own etc.
			Attribute CyclopsAccessoryColor (Color3) recolour those accessories (the King has a default)

		Any Part used as a spawn marker
			Attribute CyclopsCreature (string) "Wolf" or "AlphaWolf"
			-> replaced by the wolf, standing where the marker is.

	Outfits:  Villager, Hunter, Woodcutter, WolfRider, WolfHandler, KnightApprentice, EliteOneHorn,
	          KnightApprenticeInfected, KnightMid, KnightHigh, WolfKnight, Spearman, SpearmanShield,
	          General,
	          VillagerBlighted, WoodcutterBlighted, KnightBlighted, KnightBlightedAxe (infected elites),
	          CyclopsPrince (sub-boss), CyclopsKing, CyclopsKing3D
	Weapons:  Pitchfork, Hoe, Spade, Sickle, Scythe, HunterBow, WoodcutterAxe, WolfRiderSpear,
	          OneHornGreatsword, ApprenticeAxe, ApprenticeSword, MidAxe, MidSword, HighAxe, HighSword,
	          Spear, DragonSlayer, RadiantGreatsword, AbyssGreatsword (dual: one in each hand),
	          RoyalHalberd, EyeWarhammer, MoonBlade (dual), MoonSpear,
	          BlightScythe, CrystalMaul, BlightGreatsword, CrystalWarAxe, DragonLance,
	          SerratedSpear, SerratedSword, SerratedCleaver   (saw-toothed: apply Bleeding)
]]

local Players = game:GetService("Players")
local ServerScriptService = game:GetService("ServerScriptService")

local Kit = require(ServerScriptService:WaitForChild("CyclopsKit"))

-- Testing helper: dress every player as this outfit (nil = leave players alone).
local PLAYER_OUTFIT = nil -- e.g. "CyclopsKing"
local PLAYER_WEAPONS = {} -- e.g. { "HighSword", "HighAxe" }

local function setupNpc(model)
	local outfit = model:GetAttribute("CyclopsOutfit")
	if not outfit or model:FindFirstChild("CyclopsOutfit") then
		return
	end
	local accessories = {}
	for id in string.gmatch(model:GetAttribute("CyclopsAccessories") or "", "%d+") do
		table.insert(accessories, id)
	end
	Kit.dress(model, outfit, {
		shield = model:GetAttribute("CyclopsShield") == true,
		accessories = accessories,
		accessoryColor = model:GetAttribute("CyclopsAccessoryColor"), -- Color3 attribute, optional
	})
	local weapon = model:GetAttribute("CyclopsWeapon")
	if weapon then
		Kit.equip(model, weapon)
	end
end

local function setupMarker(marker)
	local creature = marker:GetAttribute("CyclopsCreature")
	if not creature or not marker:IsA("BasePart") then
		return
	end
	local ground = marker.CFrame * CFrame.new(0, -marker.Size.Y / 2, 0)
	local model = Kit.spawnCreature(creature, ground)
	model.Parent = marker.Parent
	marker:Destroy()
end

local function scan(instance)
	if instance:IsA("Model") then
		setupNpc(instance)
	elseif instance:IsA("BasePart") then
		setupMarker(instance)
	end
end

for _, instance in workspace:GetDescendants() do
	scan(instance)
end
workspace.DescendantAdded:Connect(function(instance)
	task.defer(scan, instance) -- let attributes and children arrive first
end)

if PLAYER_OUTFIT then
	Players.PlayerAdded:Connect(function(player)
		player.CharacterAppearanceLoaded:Connect(function(character)
			Kit.dress(character, PLAYER_OUTFIT)
			for _, weapon in PLAYER_WEAPONS do
				Kit.equip(character, weapon)
			end
		end)
	end)
end
