--[[
	Medieval Sword - server Script (put it directly inside the Tool).

	Expected Tool layout:
		Tool "MedievalSword"
		├─ Handle   (the "Grip" MeshPart, renamed to Handle)
		├─ Blade    (MeshPart)
		├─ Guard    (MeshPart)
		├─ Pommel   (MeshPart)
		└─ SwordScript (this Script)

	Click to slash. Each slash can hit each humanoid once.
]]

local Players = game:GetService("Players")

local tool = script.Parent
local handle = tool:WaitForChild("Handle")

local DAMAGE = 20
local COOLDOWN = 0.6 -- seconds between slashes
local SWING_WINDOW = 0.35 -- how long a slash can deal damage

-- Weld every other part to the Handle so the sword moves as one piece.
for _, part in tool:GetChildren() do
	if part:IsA("BasePart") and part ~= handle then
		part.Anchored = false
		part.CanCollide = false
		local weld = Instance.new("WeldConstraint")
		weld.Part0 = handle
		weld.Part1 = part
		weld.Parent = part
	end
end
handle.Anchored = false
handle.CanCollide = false

local swingSound = Instance.new("Sound")
swingSound.SoundId = "rbxasset://sounds/swordslash.wav"
swingSound.Volume = 0.6
swingSound.Parent = handle

local hitSound = Instance.new("Sound")
hitSound.SoundId = "rbxasset://sounds/swordlunge.wav"
hitSound.Volume = 0.6
hitSound.Parent = handle

local canSwing = true
local swinging = false
local hitThisSwing = {}

local function getOwner()
	local character = tool.Parent
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	return character, humanoid
end

local function onTouched(otherPart)
	if not swinging then
		return
	end
	local ownerCharacter = getOwner()
	local targetModel = otherPart:FindFirstAncestorOfClass("Model")
	if not targetModel or targetModel == ownerCharacter then
		return
	end
	local targetHumanoid = targetModel:FindFirstChildOfClass("Humanoid")
	if not targetHumanoid or targetHumanoid.Health <= 0 or hitThisSwing[targetHumanoid] then
		return
	end
	-- Don't hurt teammates when teams are in use.
	local ownerPlayer = Players:GetPlayerFromCharacter(ownerCharacter)
	local targetPlayer = Players:GetPlayerFromCharacter(targetModel)
	if ownerPlayer and targetPlayer and ownerPlayer.Team and ownerPlayer.Team == targetPlayer.Team
		and not ownerPlayer.Neutral then
		return
	end

	hitThisSwing[targetHumanoid] = true
	targetHumanoid:TakeDamage(DAMAGE)
	hitSound:Play()
end

for _, part in tool:GetChildren() do
	if part:IsA("BasePart") then
		part.Touched:Connect(onTouched)
	end
end

tool.Activated:Connect(function()
	local _, humanoid = getOwner()
	if not canSwing or not humanoid or humanoid.Health <= 0 then
		return
	end
	canSwing = false
	swinging = true
	table.clear(hitThisSwing)

	-- Classic tool slash: the default Animate script plays its slash
	-- animation when it sees this StringValue.
	local anim = Instance.new("StringValue")
	anim.Name = "toolanim"
	anim.Value = "Slash"
	anim.Parent = tool
	swingSound:Play()

	task.wait(SWING_WINDOW)
	swinging = false
	task.wait(math.max(COOLDOWN - SWING_WINDOW, 0))
	canSwing = true
end)

tool.Unequipped:Connect(function()
	swinging = false
end)
