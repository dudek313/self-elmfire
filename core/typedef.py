





type DomainID = str
type WrfFileName = str
type WrfFileNameToPath = dict[WrfFileName, Path]
type PerDomainPathList = dict[DomainID, WrfFileNameToPath]

