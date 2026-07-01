---
name: peripheral-init-failure
category: peripheral
severity: high
keywords:
  - peripheral
  - initialization
  - register config
  - clock
  - GPIO
  - timeout
  - hardware init
---

# Peripheral Initialization Failure

## Symptoms
- Peripheral not responding after initialization
- Communication interfaces (SPI, I2C, UART) not working
- GPIO pins stuck in wrong state
- Timeout errors during peripheral access
- Clock not running at expected frequency

## Debug Strategy

### Step 1: Verify clock configuration
- read_memory() at clock control registers (RCC, PLL, SCU)
- Check if peripheral clock is enabled
- Verify clock source and divider settings

### Step 2: Check peripheral registers
- get_peripheral_view() — compare actual register values with expected
- read_memory() at peripheral base address — check control/status registers
- Look for "busy" or "error" status bits

### Step 3: Verify pin configuration
- Check GPIO alternate function settings
- Verify pull-up/pull-down configuration
- Check if pins are in correct mode (input/output/alternate)

### Step 4: Trace initialization sequence
- set_breakpoint at the init function
- step("over") through each register write
- After each write, verify the register value took effect
- Some peripherals require specific write sequences or unlock patterns

### Step 5: Check for ordering dependencies
- Some peripherals must be initialized in specific order
- Clock must be enabled BEFORE configuring the peripheral
- Some registers are write-once after reset

## Common Root Causes
1. Peripheral clock not enabled (most common!)
2. Wrong GPIO alternate function mapping
3. Initialization order dependency violated
4. Write-protected registers not unlocked
5. Wrong clock source or PLL not locked
6. Pin conflict — multiple peripherals mapped to same pin
7. Missing delay after enable (peripheral needs time to stabilize)

## Fix Patterns
1. Always enable clock before any peripheral register access
2. Add clock-ready polling loop after PLL/clock changes
3. Check errata sheet for known initialization quirks
4. Use vendor HAL as reference for correct init sequence
5. Add small delay (or status polling) after peripheral enable
6. Verify with oscilloscope if clock signal is present on pins
