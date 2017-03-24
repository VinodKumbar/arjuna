package pvt.unitee.reporter.lib.generator;

import java.util.List;

import org.apache.log4j.Logger;

import com.google.gson.JsonElement;

import pvt.arjunapro.ArjunaInternal;
import pvt.arjunapro.enums.ArjunaProperty;
import pvt.arjunapro.interfaces.ReportGenerator;
import pvt.batteries.config.Batteries;
import pvt.unitee.reporter.lib.test.TestResult;
import pvt.unitee.reporter.lib.test.TestResultDeserializer;

public class TestReportGenerator extends JsonResultsReader{
	private Logger logger = Logger.getLogger(Batteries.getCentralLogName());
	private TestResultDeserializer deserializer = null;
	
	public TestReportGenerator(List<ReportGenerator> generators) throws Exception{
		super(Batteries.value(ArjunaProperty.DIRECTORY_PROJECT_RUNID_REPORT_JSON_RAW_TESTS).asString(), generators);
		deserializer = new TestResultDeserializer();
	}
	
	protected TestResult getResultObject(JsonElement jElement){
		return deserializer.process(jElement.getAsJsonObject());
	}
	
	protected void update(JsonElement jElement) throws Exception {
		TestResult reportable = this.getResultObject(jElement);
		for (ReportGenerator generator: this.getGenerators()){
			if (ArjunaInternal.displayReportGenerationInfo){
				logger.debug(String.format("%s: Updating: %s.", this.getClass().getSimpleName(), generator.getClass().getSimpleName()));
				logger.debug(String.format("Result Object: %s.", reportable.asJsonObject().toString()));
			}
			generator.update(reportable);
		}
	}

}
