package org.aema.capture;
import org.junit.Test;
import static org.junit.Assert.*;

public class ModelStoreTest {
    @Test public void acceptsGgufV3WithinBound() {
        ModelStore.validateHeader(new byte[]{'G','G','U','F',3,0,0,0}, 1024 * 1024);
    }
    @Test public void rejectsOtherVersionsTruncationAndOversizedFiles() {
        for (byte[] header : new byte[][]{{'G','G','U','F',2,0,0,0}, {1,2}, {'X','G','U','F',3,0,0,0}})
            assertThrows(IllegalArgumentException.class, () -> ModelStore.validateHeader(header, 1024 * 1024));
        byte[] header = {'G','G','U','F',3,0,0,0};
        assertThrows(IllegalArgumentException.class, () -> ModelStore.validateHeader(header, 30));
        assertThrows(IllegalArgumentException.class, () -> ModelStore.validateHeader(header, ModelStore.MAX_BYTES + 1));
    }
}
