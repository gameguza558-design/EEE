--[[
	Corrupted Greatsword - server Script (put it directly inside the Tool).

	Expected Tool layout (all MeshParts from onehorn_greatsword.fbx):
		Tool "CorruptedGreatsword"
		├─ Handle, Blade, Guard, Pommel, Blade_Glow
		└─ GreatswordScript (this Script)

	Click to slash. Each slash can hit each humanoid once.
]]

local Players = game:GetService("Players")

local tool = script.Parent
local handle = tool:WaitForChild("Handle")

local DAMAGE = 35
local COOLDOWN = 1.0 -- seconds between slashes
local SWING_WINDOW = 0.45 -- how long a slash can deal damage
local HANDLE_LENGTH = 1.3 -- studs; the whole sword is rescaled so the grip is this long
local GLOW_COLOR = Color3.fromRGB(176, 70, 255)

-- Rescale the sword around the Handle in case the import used other units.
local longest = math.max(handle.Size.X, handle.Size.Y, handle.Size.Z)
local factor = HANDLE_LENGTH / longest
if math.abs(factor - 1) > 0.01 then
	for _, part in tool:GetChildren() do
		if part:IsA("BasePart") and part ~= handle then
			local rel = handle.CFrame:ToObjectSpace(part.CFrame)
			part.Size *= factor
			part.CFrame = handle.CFrame * (rel - rel.Position + rel.Position * factor)
		end
	end
	handle.Size *= factor
end

for _, part in tool:GetChildren() do
	if part:IsA("BasePart") then
		part.Anchored = false
		part.CanCollide = false
		part.Massless = part ~= handle
		if string.match(part.Name, "_Glow$") then
			part.TextureID = ""
			part.Material = Enum.Material.Neon
			part.Color = GLOW_COLOR
		end
		if part ~= handle then
			local weld = Instance.new("WeldConstraint")
			weld.Part0 = handle
			weld.Part1 = part
			weld.Parent = part
		end
	end
end

local swingSound = Instance.new("Sound")
swingSound.SoundId = "rbxasset://sounds/swordslash.wav"
swingSound.Volume = 0.7
swingSound.PlaybackSpeed = 0.8
swingSound.Parent = handle

local hitSound = Instance.new("Sound")
hitSound.SoundId = "rbxasset://sounds/swordlunge.wav"
hitSound.Volume = 0.7
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
