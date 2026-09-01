// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package camera

import "strings"

// mipiDevicePatterns contains known MIPI camera driver patterns and device identifiers.
var mipiDevicePatterns = map[string]struct{}{
	"avstream":                          {},
	"ov08x40":                           {},
	"ovti08f4":                          {},
	"ovti08x4":                          {},
	"ovti":                              {},
	"vd55g0":                            {},
	"vd55g1":                            {},
	"vd55g":                             {},
	"iacamera":                          {},
	"iaisp":                             {},
	"iactrllogic":                       {},
	"iaflash":                           {},
	"intc1070":                          {},
	"intc1020":                          {},
	"intc1065":                          {},
	"intc1095":                          {},
	"int3470":                           {},
	"int3471":                           {},
	"int3472":                           {},
	"int3474":                           {},
	"int3477":                           {},
	"int347e":                           {},
	"int3480":                           {},
	"int3482":                           {},
	"hm2170":                            {},
	"hm11b1":                            {},
	"hi556":                             {},
	"imx":                               {},
	"gc5035":                            {},
	"ov2740":                            {},
	"ov9734":                            {},
	"ov8856":                            {},
	"mipi":                              {},
	"intel(r) mtl avstream":             {},
	"intel(r) ptl avstream":             {},
	"intel(r) lnl avstream":             {},
	"intel(r) control logic":            {},
	"intel(r) imaging signal processor": {},
	"intel(r) camera flash led":         {},
	"intel(r) usbi2c":                   {},
	"intel(r) usbgpio":                  {},
	"intel(r) usbio":                    {},
	"intel usbio bridge":                {},
	"usbi2c":                            {},
	"usbgpio":                           {},
	"usbio bridge":                      {},
	"camera sensor":                     {},
	"7d19":                              {},
	"645d":                              {},
	"465d":                              {},
	"a75d":                              {},
	"9a19":                              {},
	"b719":                              {},
}

var sensorPatterns = []string{
	"sensor", "ov08x40", "ovti", "vd55g", "hm11b", "hm217", "hi556",
	"imx", "gc5035", "ov2740", "ov9734", "ov8856", "int3472", "int3474",
}

var ipuPatterns = []string{
	"imaging signal processor", "iaisp", "ipu", "7d19", "645d", "465d",
	"a75d", "9a19", "b719",
}

var avstreamPatterns = []string{
	"avstream", "iacamera", "intc1070", "intc1020", "intc1065", "intc1095",
}

var controlLogicPatterns = []string{
	"control logic", "iactrllogic", "flash", "iaflash", "int3480", "int3482",
	"usbi2c", "usbgpio", "usbio",
}

func isSensor(identifier string) bool {
	return containsAny(identifier, sensorPatterns)
}

func isIPU(identifier string) bool {
	return containsAny(identifier, ipuPatterns)
}

func isAVStream(identifier string) bool {
	return containsAny(identifier, avstreamPatterns)
}

func isControlLogic(identifier string) bool {
	return containsAny(identifier, controlLogicPatterns)
}

func containsAny(s string, patterns []string) bool {
	for _, p := range patterns {
		if strings.Contains(s, p) {
			return true
		}
	}
	return false
}
