#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""IB Fundamental data"""
__all__ = ["CompanyFinancials", "FundamentalData", "objects", "utils"]
__author__ = "Gonzalo Sáenz"
__copyright__ = "Copyright 2024 Gonzalo Sáenz"
__credits__ = ["Gonzalo Sáenz"]
__license__ = "Apache 2.0"
__version__ = "0.0.6"
__maintainer__ = "Gonzalo Sáenz"


from . import objects, utils
from .fundamental import CompanyFinancials, FundamentalData
