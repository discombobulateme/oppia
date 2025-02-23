// Copyright 2018 The Oppia Authors. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS-IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * @fileoverview Unit tests for IdGenerationService.
 */

// TODO(#7222): Remove the following block of unnnecessary imports once
// the code corresponding to the spec is upgraded to Angular 8.
import { UpgradedServices } from 'services/UpgradedServices';
// ^^^ This block is to be removed.

require('services/id-generation.service.ts');

describe('IdGenerationService', function() {
  var IdGenerationService = null;

  beforeEach(angular.mock.module('oppia'));
  beforeEach(angular.mock.module('oppia', function($provide) {
    var ugs = new UpgradedServices();
    for (let [key, value] of Object.entries(ugs.upgradedServices)) {
      $provide.value(key, value);
    }
  }));
  beforeEach(angular.mock.inject(function($injector) {
    IdGenerationService = $injector.get('IdGenerationService');
  }));

  it('should generate a random id of fixed length', function() {
    expect(IdGenerationService.generateNewId()).toMatch(/^[a-z0-9]{10}$/);
  });

  it('should generate two different ids', function() {
    var id1 = IdGenerationService.generateNewId();
    var id2 = IdGenerationService.generateNewId();
    expect(id1).not.toEqual(id2);
  });
});
