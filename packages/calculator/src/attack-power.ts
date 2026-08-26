import type { AttackPowerCheckpointsContract, NormalizedBuild } from '@weather-artist/contracts';
import { dec, decimalString } from './decimal.js';

export type AttackPowerCheckpoints = AttackPowerCheckpointsContract;

export function reconstructAttackPower(build: NormalizedBuild): AttackPowerCheckpoints {
  const equipmentMainStat = dec(build.equipment.mainStat);
  const accountMainStatFlat = dec(build.calculationInputs.accountBonuses.flatMainStat);
  const baseMainStat = equipmentMainStat.plus(accountMainStatFlat);
  const avatarMainStatPercent = dec(build.avatars.mainStatPercent);
  const petMainStatPercent = dec(build.calculationInputs.pet.mainStatPercent);
  const finalMainStat = baseMainStat.times(
    dec(1).plus(avatarMainStatPercent).plus(petMainStatPercent)
  );
  const baseWeaponAttack = dec(build.equipment.baseWeaponAttack);
  const equipmentWeaponAttackFlat = dec(build.equipment.weaponAttackFlat);
  const arkGridWeaponAttackFlat = dec(build.arkGrid.weaponAttackFlat);
  const weaponAttackSubtotal = baseWeaponAttack.plus(equipmentWeaponAttackFlat).plus(arkGridWeaponAttackFlat);
  const equipmentWeaponAttackPercent = dec(build.equipment.weaponAttackPercent);
  const karmaWeaponAttackPercent = dec(build.arkPassive.karmaWeaponAttackPercent);
  const arkGridWeaponAttackPercent = dec(build.arkGrid.weaponAttackPercent);
  const weaponAttackPercent = equipmentWeaponAttackPercent.plus(karmaWeaponAttackPercent).plus(arkGridWeaponAttackPercent);
  const finalWeaponAttack = weaponAttackSubtotal.times(dec(1).plus(weaponAttackPercent));
  if (finalMainStat.isNegative() || finalWeaponAttack.isNegative()) {
    throw new Error('Main stat and weapon attack must not be negative.');
  }
  const rootAttackPower = finalMainStat.times(finalWeaponAttack).div(6).sqrt();
  const armletBaseAttackFlat = dec(build.equipment.baseAttackPowerFlat);
  const gemsBaseAttackPercent = dec(build.gems.baseAttackPercent);
  const stoneBaseAttackPercent = dec(build.engravings.stoneBaseAttackPercent);
  const equipmentBaseAttackPercent = dec(build.equipment.baseAttackPowerPercent);
  const baseAttackPercent = gemsBaseAttackPercent.plus(stoneBaseAttackPercent).plus(equipmentBaseAttackPercent);
  const afterBaseAttackPercent = rootAttackPower
    .plus(armletBaseAttackFlat)
    .times(dec(1).plus(baseAttackPercent));
  const equipmentAttackPowerFlat = dec(build.equipment.attackPowerFlat);
  const arkGridAttackPowerFlat = dec(build.arkGrid.attackPowerFlat);
  const attackPowerFlat = equipmentAttackPowerFlat.plus(arkGridAttackPowerFlat);
  const adrenaline = dec(build.engravings.effects['아드레날린']?.attackPowerPercent ?? 0);
  const equipmentAttackPowerPercent = dec(build.equipment.attackPowerPercent);
  const arkGridAttackPowerPercent = dec(build.arkGrid.attackPowerPercent);
  const attackPowerPercent = equipmentAttackPowerPercent
    .plus(adrenaline)
    .plus(arkGridAttackPowerPercent);
  const final = afterBaseAttackPercent
    .plus(attackPowerFlat)
    .times(dec(1).plus(attackPowerPercent));
  const profileAttackPower = dec(build.profile.profileAttackPower);
  return {
    equipmentMainStat: decimalString(equipmentMainStat),
    accountMainStatFlat: decimalString(accountMainStatFlat),
    baseMainStat: decimalString(baseMainStat),
    avatarMainStatPercent: decimalString(avatarMainStatPercent),
    petMainStatPercent: decimalString(petMainStatPercent),
    finalMainStat: decimalString(finalMainStat),
    baseWeaponAttack: decimalString(baseWeaponAttack),
    equipmentWeaponAttackFlat: decimalString(equipmentWeaponAttackFlat),
    arkGridWeaponAttackFlat: decimalString(arkGridWeaponAttackFlat),
    weaponAttackSubtotal: decimalString(weaponAttackSubtotal),
    equipmentWeaponAttackPercent: decimalString(equipmentWeaponAttackPercent),
    weaponAttackPercent: decimalString(weaponAttackPercent),
    karmaWeaponAttackPercent: decimalString(karmaWeaponAttackPercent),
    arkGridWeaponAttackPercent: decimalString(arkGridWeaponAttackPercent),
    finalWeaponAttack: decimalString(finalWeaponAttack),
    rootAttackPower: decimalString(rootAttackPower),
    armletBaseAttackFlat: decimalString(armletBaseAttackFlat),
    gemsBaseAttackPercent: decimalString(gemsBaseAttackPercent),
    stoneBaseAttackPercent: decimalString(stoneBaseAttackPercent),
    equipmentBaseAttackPercent: decimalString(equipmentBaseAttackPercent),
    baseAttackPercent: decimalString(baseAttackPercent),
    afterBaseAttackPercent: decimalString(afterBaseAttackPercent),
    equipmentAttackPowerFlat: decimalString(equipmentAttackPowerFlat),
    arkGridAttackPowerFlat: decimalString(arkGridAttackPowerFlat),
    attackPowerFlat: decimalString(attackPowerFlat),
    equipmentAttackPowerPercent: decimalString(equipmentAttackPowerPercent),
    adrenalineAttackPowerPercent: decimalString(adrenaline),
    arkGridAttackPowerPercent: decimalString(arkGridAttackPowerPercent),
    attackPowerPercent: decimalString(attackPowerPercent),
    profileAttackPower: decimalString(profileAttackPower),
    final: decimalString(final),
    usedForDamage: decimalString(final),
    usedForDamageSource: final.eq(profileAttackPower) ? 'CALCULATED' : 'CALCULATED_OFFICIAL'
  };
}
